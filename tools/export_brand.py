#!/usr/bin/env python3
"""Generate the FOAB brand SVGs and PNG exports into img/brand/.

Single source of truth for the mark (gear, outlined "FOAB" letters, forks),
cleaned up from the original logo pack. Run: python3 tools/export_brand.py
PNG export needs Pillow and a Chromium binary (CHROME env var to override).
"""
import math
import os
import shutil
import subprocess
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "img", "brand")
INK = "#111111"
YELLOW = "#F5B91B"
WHITE = "#FFFFFF"

# Mark geometry lives in a 1000x1000 space centred on (500, 500).
# Ring: radius 210, 40 wide (inner edge 190). Letters stay within radius ~170.
LETTERS = " ".join([
    # F
    "M358 400H420V420H378V445H410V465H378V510H358Z",
    # O (outer stadium + counter)
    "M432 431A31 31 0 0 1 494 431V479A31 31 0 0 1 432 479Z"
    "M452 431A11 11 0 0 1 474 431V479A11 11 0 0 1 452 479Z",
    # A (outer + counter)
    "M506 510L526 400H548L568 510H548L544 488H530L526 510Z"
    "M531.6 470H542.4L537 432Z",
    # B (outer + two counters)
    "M580 400H610A26 26 0 0 1 620.5 449.8A31 31 0 0 1 611 510H580Z"
    "M600 418H610A8 8 0 0 1 610 434H600Z"
    "M600 466H611A13 13 0 0 1 611 492H600Z",
])
FORKS = [
    "M454 530V640L382 690H344V664L421 613V530Z",
    "M546 530V640L618 690H656V664L579 613V530Z",
]


def teeth(fill, radius=255, size=56):
    out = []
    for i in range(12):
        a = math.radians(i * 30)
        cx, cy = 500 + radius * math.cos(a), 500 + radius * math.sin(a)
        h = size / 2
        out.append(
            f'<rect x="{cx - h:.1f}" y="{cy - h:.1f}" width="{size}" height="{size}" '
            f'fill="{fill}" transform="rotate({i * 30} {cx:.1f} {cy:.1f})"/>'
        )
    return "".join(out)


def svg(view_box, body, label="FOAB"):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" role="img" aria-label="{label}">'
        f"{body}</svg>\n"
    )


def mark(ink, letters=True, backdrop=None, ring_width=40, ring_r=210, fork_transform=""):
    parts = []
    if backdrop:
        parts.append(f'<circle cx="500" cy="500" r="{ring_r + ring_width / 2}" fill="{backdrop}"/>')
    parts.append(teeth(ink))
    parts.append(f'<circle cx="500" cy="500" r="{ring_r}" fill="none" stroke="{ink}" stroke-width="{ring_width}"/>')
    if letters:
        parts.append(f'<path d="{LETTERS}" fill="{ink}" fill-rule="evenodd"/>')
    g = f'<g transform="{fork_transform}">' if fork_transform else "<g>"
    g += "".join(
        f'<path d="{d}" fill="{YELLOW}" stroke="{INK}" stroke-width="13" stroke-linejoin="round"/>' for d in FORKS
    )
    parts.append(g + "</g>")
    return "".join(parts)


TIGHT = "206 206 588 588"


def write_svgs():
    os.makedirs(OUT, exist_ok=True)
    files = {
        # Dark ink on transparent: light backgrounds.
        "logo.svg": svg(TIGHT, mark(INK)),
        # White gear and letters: the black header / dark backgrounds.
        "logo-light.svg": svg(TIGHT, mark(WHITE)),
        # Self-contained mark on a white disc: works on any background.
        "icon.svg": svg(TIGHT, mark(INK, backdrop=WHITE)),
        # No letters, heavier ring, forks enlarged and centred: legible at 16-32px.
        "favicon.svg": svg(
            "196 196 608 608",
            mark(INK, letters=False, backdrop=WHITE, ring_width=64, ring_r=200,
                 fork_transform="translate(500 500) scale(1.25) translate(-500 -605)"),
        ),
    }
    for name, content in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(content)


def chrome():
    return os.environ.get("CHROME") or shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")


def screenshot(html, width, height, out_png):
    # Chromium snap can only read files under $HOME, so the temp page lives in the repo's scratch dir.
    scratch = os.path.join(ROOT, ".superpowers", "tmp")
    os.makedirs(scratch, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=scratch, delete=False, encoding="utf-8") as f:
        f.write(html)
        page = f.name
    try:
        subprocess.run(
            [chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
             f"--window-size={width},{height}", "--default-background-color=00000000",
             f"--screenshot={out_png}", "file://" + page],
            check=True, capture_output=True, timeout=60,
        )
    finally:
        os.unlink(page)
    with Image.open(out_png) as im:
        if im.size != (width, height):
            im.crop((0, 0, width, height)).save(out_png)


def page(body, bg="transparent"):
    return (
        "<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:%s}"
        "body{font-family:system-ui,'DejaVu Sans',sans-serif}</style>%s" % (bg, body)
    )


def write_pngs():
    favicon = open(os.path.join(OUT, "favicon.svg"), encoding="utf-8").read()
    big = os.path.join(OUT, ".favicon-512.png")
    screenshot(page(f'<div style="width:512px;height:512px">{favicon.replace("<svg ", "<svg width=512 height=512 ")}</div>'), 512, 512, big)
    with Image.open(big) as im:
        im = im.convert("RGBA")
        im.resize((32, 32), Image.LANCZOS).save(os.path.join(OUT, "favicon-32.png"))
        apple = Image.new("RGBA", (180, 180), WHITE)
        icon = im.resize((156, 156), Image.LANCZOS)
        apple.alpha_composite(icon, (12, 12))
        apple.convert("RGB").save(os.path.join(OUT, "apple-touch-icon.png"))
    os.unlink(big)

    logo_light = open(os.path.join(OUT, "logo-light.svg"), encoding="utf-8").read()
    stripes = f"repeating-linear-gradient(-45deg,{YELLOW} 0 22px,{INK} 22px 44px)"
    og = page(
        f'<div style="width:1200px;height:630px;background:{INK};color:#fff;position:relative;'
        f'display:flex;align-items:center;gap:56px;padding:0 80px;box-sizing:border-box">'
        f'<div style="width:340px;height:340px;flex:none">{logo_light.replace("<svg ", "<svg width=340 height=340 ")}</div>'
        f'<div><div style="color:{YELLOW};font-weight:700;letter-spacing:4px;font-size:26px;text-transform:uppercase">'
        f"Porodična firma · 15+ godina</div>"
        f'<div style="font-weight:800;font-size:68px;line-height:1.05;margin:14px 0 22px">Servis viljuškara<br>širom Srbije</div>'
        f'<div style="font-size:40px;font-weight:700">064 119 6048 · foab.rs</div></div>'
        f'<div style="position:absolute;left:0;right:0;bottom:0;height:22px;background:{stripes}"></div></div>',
        bg=INK,
    )
    screenshot(og, 1200, 630, os.path.join(OUT, "og-image.png"))
    with Image.open(os.path.join(OUT, "og-image.png")) as im:
        im.convert("RGB").save(os.path.join(OUT, "og-image.png"))


def write_ico():
    # Some crawlers and old browsers request /favicon.ico regardless of <link rel="icon">.
    favicon = open(os.path.join(OUT, "favicon.svg"), encoding="utf-8").read()
    big = os.path.join(OUT, ".favicon-256.png")
    screenshot(page(f'<div style="width:256px;height:256px">{favicon.replace("<svg ", "<svg width=256 height=256 ")}</div>'), 256, 256, big)
    with Image.open(big) as im:
        im.convert("RGBA").save(os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    os.unlink(big)


if __name__ == "__main__":
    write_svgs()
    write_pngs()
    write_ico()
    print("wrote", ", ".join(sorted(os.listdir(OUT))))
