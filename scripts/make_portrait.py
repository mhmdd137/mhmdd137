"""Turn a photo into a self-typing ASCII portrait.

Brightness follows the photo: lit skin prints bright and dense, dark hair and
beard print as a dim texture, so the proportions stay true to the photo.

Run once per photo, on your own machine (needs heavier libraries than the
daily workflow):

    pip install pillow numpy opencv-python onnxruntime
    python scripts/make_portrait.py photo.jpg 448,261,1162,1146 354,372,262,330,650

Arguments:
  1. the photo
  2. crop box in pixels: left,top,right,bottom (head and shoulders, ~4 wide by 5 tall)
  3. optional head ellipse inside the crop: cx,cy,rx,ry,chin_y. Anything outside
     it (and above the chin) is dropped, which keeps background objects that
     touch the hair out of the cut-out.

The first run downloads a person-segmentation model (U2-Net, ~170 MB).
"""
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageOps

from theme import AMBER, INSET, PAD, PORTRAIT, base_css, esc, panel, scanlines, write

WIDTH, HEIGHT = 350, 460
AREA_X, AREA_Y, AREA_W = PAD, 54, WIDTH - 2 * PAD
COLS = 110
RAMP = " .`'-:;~=+*ox#%@"  # sparse -> dense
LEVELS = 8  # brightness steps
OP_MIN, OP_POW = 0.22, 0.75  # opacity of the dimmest step, and the curve
FADE_FROM = 0.72  # shoulders fade out below this fraction of the height

MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx"
MODEL = Path.home() / ".cache" / "u2net_human_seg.onnx"


def person_mask(img: Image.Image) -> np.ndarray:
    """0..1 mask of the person, from the U2-Net human segmentation model."""
    if not MODEL.exists():
        MODEL.parent.mkdir(parents=True, exist_ok=True)
        print("downloading model ...")
        urllib.request.urlretrieve(MODEL_URL, MODEL)
    sess = ort.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])
    x = np.asarray(img.resize((320, 320), Image.LANCZOS)).astype(np.float32)
    x = x / x.max()
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    pred = sess.run(None, {sess.get_inputs()[0].name: x})[0][0, 0]
    pred = (pred - pred.min()) / (pred.max() - pred.min())
    return cv2.resize(pred, img.size, interpolation=cv2.INTER_LINEAR)


def cut_out(img: Image.Image, head) -> np.ndarray:
    alpha = person_mask(img)

    # Keep only the blob that holds the face (drops background bits the model grabbed)
    k = max(3, int(alpha.shape[1] * 0.03)) | 1
    blob = cv2.morphologyEx((alpha > 0.5).astype(np.uint8), cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
    n, lab = cv2.connectedComponents(blob)
    if n > 1:
        keep = lab[int(alpha.shape[0] * 0.45), int(alpha.shape[1] * 0.5)] or np.bincount(lab[blob > 0]).argmax()
        alpha = alpha * cv2.dilate((lab == keep).astype(np.uint8), np.ones((k, k), np.uint8))
        alpha = cv2.GaussianBlur(alpha.astype(np.float32), (0, 0), 2)

    if head:  # head ellipse + everything below the chin
        hx, hy, rx, ry, chin = head
        yy, xx = np.mgrid[0 : alpha.shape[0], 0 : alpha.shape[1]]
        inside = (((xx - hx) / rx) ** 2 + ((yy - hy) / ry) ** 2 <= 1) | (yy > chin)
        alpha = alpha * cv2.GaussianBlur(inside.astype(np.float32), (0, 0), 6)
    return alpha


def tones(path: str, box, head) -> np.ndarray:
    """Brightness 0..1 per character cell (0 = blank)."""
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    if box:
        img = img.crop(box)
    alpha = cut_out(img, head)

    gray = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8)).apply(gray).astype(np.float32) / 255.0

    h, w = gray.shape
    cell_w = AREA_W / COLS
    line_h = cell_w / 0.6 * 1.1
    rows = round(COLS * (h / w) * (cell_w / line_h))
    g = cv2.resize(gray, (COLS, rows), interpolation=cv2.INTER_AREA)
    a = cv2.resize(alpha, (COLS, rows), interpolation=cv2.INTER_AREA)

    lo, hi = np.percentile(g[a > 0.5], [2, 98])  # tones measured on the person only
    v = np.clip((g - lo) / (hi - lo), 0, 1) ** 0.85
    v = 0.2 + 0.8 * v  # dark hair and beard stay visible as a dim texture
    v *= np.clip((a - 0.35) / 0.4, 0, 1)  # background -> nothing, soft edge
    f0 = int(rows * FADE_FROM)
    for r in range(f0, rows):
        v[r] *= max(0.0, 1 - (r - f0) / (rows - f0)) ** 1.3
    v[v < 0.06] = 0
    while len(v) and not v[-1].any():  # drop empty rows left by the fade
        v = v[:-1]
    return v


def build(v: np.ndarray) -> str:
    cell_w = AREA_W / COLS
    font = cell_w / 0.6
    line_h = font * 1.1
    top = AREA_Y + max(0.0, (HEIGHT - INSET - 14 - AREA_Y - len(v) * line_h) / 2)
    clips, rows = [], []
    for i, row in enumerate(v):
        # group neighbouring characters with the same brightness into one tspan
        spans, cur, buf = [], None, ""
        for val in row:
            ch = RAMP[int(round(val * (len(RAMP) - 1)))]
            lvl = int(round(val * (LEVELS - 1)))
            if lvl != cur and buf:
                spans.append((cur, buf))
                buf = ""
            cur, buf = lvl, buf + ch
        spans.append((cur, buf))
        tspans = "".join(
            f'<tspan fill-opacity="{OP_MIN + (1 - OP_MIN) * (lv / (LEVELS - 1)) ** OP_POW:.2f}">{esc(s)}</tspan>'
            for lv, s in spans
        )

        y = top + i * line_h
        begin, dur = 0.3 + i * 0.03, 0.24
        clips.append(
            f'<clipPath id="r{i}"><rect x="{AREA_X}" y="{y:.2f}" width="0" height="{line_h + 0.5:.2f}">'
            f'<animate attributeName="width" from="0" to="{AREA_W}" begin="{begin:.3f}s" dur="{dur}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
        rows.append(
            f'<text clip-path="url(#r{i})" x="{AREA_X}" y="{y + font:.2f}" textLength="{AREA_W}" '
            f'lengthAdjust="spacing" xml:space="preserve">{tspans}</text>'
            # block cursor riding the wipe edge, gone once the row is printed
            f'<rect x="{AREA_X}" y="{y + 0.5:.2f}" width="{cell_w:.2f}" height="{line_h:.2f}" fill="{AMBER}" opacity="0">'
            f'<set attributeName="opacity" to="0.9" begin="{begin:.3f}s"/>'
            f'<animate attributeName="x" from="{AREA_X}" to="{AREA_X + AREA_W - cell_w:.2f}" begin="{begin:.3f}s" dur="{dur}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + dur:.3f}s"/></rect>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="ASCII portrait of Mohammed Ziada">
  <style>{base_css()}
    .a text{{font-size:{font:.2f}px;fill:{PORTRAIT};white-space:pre;}}
  </style>{panel(WIDTH, HEIGHT, "cat portrait.txt")}
  <defs>{''.join(clips)}</defs>
  <g class="a">{''.join(rows)}</g>
  {scanlines(WIDTH, HEIGHT)}
</svg>
"""


if __name__ == "__main__":
    crop = tuple(int(n) for n in sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    head = tuple(int(n) for n in sys.argv[3].split(",")) if len(sys.argv) > 3 else None
    print("wrote", write("portrait.svg", build(tones(sys.argv[1], crop, head))))
