#!/usr/bin/env python3
"""Structural checks for the FOAB static site. Run: python3 tests/check_site.py"""
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


def path(rel):
    return os.path.join(ROOT, rel)


def load(rel):
    with open(path(rel), encoding="utf-8") as f:
        return f.read()


class Doc(HTMLParser):
    """Flat list of elements as dicts: tag, attrs, text (all nested text)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        el = {"tag": tag, "attrs": {k: (v if v is not None else "") for k, v in attrs}, "text": ""}
        self.elements.append(el)
        if tag not in VOID:
            self.stack.append(el)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        for el in self.stack:
            el["text"] += data

    def find_all(self, tag=None, **attrs):
        out = []
        for el in self.elements:
            if tag and el["tag"] != tag:
                continue
            ok = True
            for k, v in attrs.items():
                k = k.rstrip("_").replace("_", "-")
                if v is True:
                    ok = k in el["attrs"]
                elif el["attrs"].get(k) != v:
                    ok = False
                if not ok:
                    break
            if ok:
                out.append(el)
        return out

    def find(self, tag=None, **attrs):
        found = self.find_all(tag, **attrs)
        return found[0] if found else None

    def has_class(self, cls):
        return [e for e in self.elements if cls in e["attrs"].get("class", "").split()]


def parse(rel):
    d = Doc()
    d.feed(load(rel))
    return d


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


# --- tests -----------------------------------------------------------------

def test_cname():
    check(load("CNAME").strip() == "foab.rs", "CNAME must be foab.rs")


def test_no_angular_left():
    for rel in ("angular.json", "package.json", "src"):
        check(not os.path.exists(path(rel)), f"{rel} should be removed")


BRAND_SVGS = ["logo.svg", "logo-light.svg", "icon.svg", "favicon.svg"]


def test_brand_svgs():
    for name in BRAND_SVGS:
        src = load(f"img/brand/{name}")
        check("<text" not in src, f"{name}: lettering must be outlined paths, not <text>")
        check("viewBox=" in src, f"{name}: missing viewBox")


def test_brand_pngs():
    from PIL import Image
    for name, size in {"favicon-32.png": (32, 32), "apple-touch-icon.png": (180, 180), "og-image.png": (1200, 630)}.items():
        with Image.open(path(f"img/brand/{name}")) as im:
            check(im.size == size, f"{name}: expected {size}, got {im.size}")


TEL = "tel:+381641196048"
MAP_SRC = ("https://www.google.com/maps/embed/v1/place?key=AIzaSyAg0Ia7fjTQmBfxA5rz2Mk3sf_Knqtiguo"
           "&q=Cara+Du%C5%A1ana+58%2C+22324+Be%C5%A1ka%2C+Serbia")
SECTIONS = ["usluge", "o-nama", "kontakt"]
FIELDS = {"ime": True, "firma": False, "kontakt": True, "poruka": True}
HTML_PAGES = ["index.html", "hvala.html", "en/index.html", "en/thank-you.html", "404.html"]


def meta(doc, **attrs):
    el = doc.find("meta", **attrs)
    return el["attrs"].get("content", "") if el else ""


def page_basics(rel, lang, other_lang, other_href):
    d = parse(rel)
    check(d.find("html")["attrs"].get("lang") == lang, f"{rel}: lang should be {lang}")
    check("FOAB" in d.find("title")["text"], f"{rel}: title should mention FOAB")
    check(meta(d, name="description"), f"{rel}: missing meta description")
    check(meta(d, name="viewport"), f"{rel}: missing viewport")
    check(d.find("link", rel="alternate", hreflang=other_lang, href=other_href), f"{rel}: missing hreflang {other_lang}")
    check(d.find("link", rel="alternate", hreflang=lang), f"{rel}: missing self hreflang")
    for prop in ("og:title", "og:description"):
        check(meta(d, property=prop), f"{rel}: missing {prop}")
    check(meta(d, property="og:image") == "https://foab.rs/img/brand/og-image.png", f"{rel}: og:image")
    check(d.find("link", rel="icon", href="/img/brand/favicon.svg"), f"{rel}: missing svg favicon")
    check(d.find("link", rel="apple-touch-icon"), f"{rel}: missing apple-touch-icon")
    return d


def form_checks(rel, subject, redirect):
    d = parse(rel)
    form = d.find("form", id="contact-form")
    check(form, f"{rel}: no #contact-form")
    a = form["attrs"]
    check(a.get("action") == "https://api.web3forms.com/submit" and a.get("method", "").upper() == "POST", f"{rel}: form action/method")
    for k in ("data-msg-sending", "data-msg-success", "data-msg-error"):
        check(a.get(k), f"{rel}: form needs non-empty {k}")
    hidden = {e["attrs"].get("name"): e["attrs"].get("value") for e in d.find_all("input", type="hidden")}
    check(hidden.get("access_key") == "0ffe675e-1961-474c-b6b7-e6931ef29d6a", f"{rel}: access_key must be the real Web3Forms key")
    check(hidden.get("subject") == subject, f"{rel}: subject should be {subject!r}")
    check(hidden.get("from_name") == "FOAB sajt", f"{rel}: from_name")
    check(hidden.get("redirect") == redirect, f"{rel}: redirect should be {redirect}")
    check(d.find("input", type="checkbox", name="botcheck"), f"{rel}: botcheck honeypot missing")
    for name, required in FIELDS.items():
        el = d.find("textarea" if name == "poruka" else "input", name=name)
        check(el, f"{rel}: field {name} missing")
        check(("required" in el["attrs"]) == required, f"{rel}: field {name} required={required}")
        check(el["attrs"].get("id") and d.find("label", for_=el["attrs"]["id"]), f"{rel}: field {name} needs a label")
    check(d.has_class("form-status"), f"{rel}: .form-status missing")
    return d


def test_sr_basics():
    page_basics("index.html", "sr", "en", "https://foab.rs/en/")


def test_sr_phone():
    d = parse("index.html")
    check(len(d.find_all("a", href=TEL)) >= 3, "index.html: need >=3 tel links")
    check("064 119 6048" in load("index.html"), "index.html: display phone missing")
    check(d.has_class("call-bar") and d.has_class("call-bar")[0]["attrs"].get("href") == TEL, "call bar must be a tel link")


def test_sr_sections():
    d = parse("index.html")
    for s in SECTIONS:
        check(d.find(id=s), f"index.html: section #{s} missing")
        nav = d.find("nav", id="site-nav")
        check(nav is not None, "nav#site-nav missing")
    hrefs = {e["attrs"].get("href") for e in d.find_all("a")}
    for s in SECTIONS:
        check(f"#{s}" in hrefs, f"index.html: nav link #{s} missing")
    check(d.find("button", aria_controls="site-nav"), "nav toggle missing")
    check(d.find("a", href="/en/", hreflang="en"), "lang switch to /en/ missing")


def test_sr_form():
    form_checks("index.html", "Novi upit sa sajta foab.rs", "https://foab.rs/hvala.html")


def map_check(rel):
    d = parse(rel)
    frames = d.find_all("iframe")
    check(len(frames) == 1, f"{rel}: expected one iframe")
    a = frames[0]["attrs"]
    check(a.get("src") == MAP_SRC, f"{rel}: map src mismatch: {a.get('src')}")
    check(a.get("loading") == "lazy" and a.get("title"), f"{rel}: map needs loading=lazy and title")
    check("width" not in a, f"{rel}: map iframe must not have a fixed width")


def test_sr_map():
    map_check("index.html")


def jsonld(rel):
    d = parse(rel)
    s = d.find("script", type="application/ld+json")
    check(s, f"{rel}: JSON-LD missing")
    data = json.loads(s["text"])
    check(data["@type"] == "LocalBusiness", "@type")
    check(data["telephone"] == "+381641196048", "telephone")
    check(data["email"] == "foab.nesa@gmail.com", "email")
    addr = data["address"]
    check(addr["streetAddress"] == "Cara Dušana 58" and addr["addressLocality"] == "Beška" and addr["postalCode"] == "22324", "address")
    check(data["areaServed"] == "Serbia", "areaServed")


def test_sr_jsonld():
    jsonld("index.html")


def test_no_fake_or_template_text():
    for rel in HTML_PAGES:
        if not os.path.exists(path(rel)):
            continue
        low = load(rel).lower()
        for bad in ("lorem", "speeds up development", "06x", "xxx"):
            check(bad not in low, f"{rel}: contains {bad!r}")


def test_call_bar_padding():
    css = load("css/style.css")
    blocks = re.findall(r"@media\s*\(max-width:\s*767px\)\s*\{(.*?)\n\}", css, re.S)
    check(blocks, "no @media (max-width: 767px) block")
    check(any(re.search(r"body\s*\{[^}]*padding-bottom", b) for b in blocks), "body padding-bottom missing in phone media block")


def test_hvala():
    d = parse("hvala.html")
    check(d.find("html")["attrs"].get("lang") == "sr", "hvala lang")
    check(d.find("a", href="/"), "hvala: link back to /")
    check(d.find("a", href=TEL), "hvala: phone link")


def test_en_parity():
    page_basics("en/index.html", "en", "sr", "https://foab.rs/")
    sr, en = parse("index.html"), parse("en/index.html")
    for s in SECTIONS:
        check(en.find(id=s), f"en: section #{s} missing (ids must match SR)")
    check(len(en.find_all("a", href=TEL)) == len(sr.find_all("a", href=TEL)), "en: tel link count differs from SR")
    check("+381 64 119 6048" in load("en/index.html"), "en: display phone missing")
    check(en.find("a", href="/", hreflang="sr"), "en: lang switch to / missing")
    check(en.has_class("call-bar"), "en: call bar missing")
    check(en.find("header", data_site=True), "en: header needs data-site for JS")
    form_checks("en/index.html", "New inquiry from foab.rs", "https://foab.rs/en/thank-you.html")
    map_check("en/index.html")
    jsonld("en/index.html")
    d = parse("en/thank-you.html")
    check(d.find("html")["attrs"].get("lang") == "en", "thank-you lang")
    check(d.find("a", href="/en/"), "thank-you: link back to /en/")
    check(d.find("a", href=TEL), "thank-you: phone link")


IMAGES = ["hero", "service-forklift", "service-rental", "service-tractor", "about"]


def test_images():
    credits = load("img/CREDITS.md")
    for name in IMAGES:
        rel = f"img/{name}.webp"
        check(os.path.exists(path(rel)), f"{rel} missing")
        check(os.path.getsize(path(rel)) <= 200 * 1024, f"{rel} over 200 KB")
        check(f"{name}.webp" in credits, f"{rel} not listed in CREDITS.md")
    for rel in ("index.html", "en/index.html"):
        for img in parse(rel).find_all("img"):
            a = img["attrs"]
            check("alt" in a and a.get("width") and a.get("height"), f"{rel}: <img src={a.get('src')}> needs alt, width, height")


def test_photo_credits_visible():
    # CC BY / BY-SA placeholder photos must be attributed on the page itself while they are in use.
    credits = load("img/CREDITS.md")
    artists = re.findall(r"\" by (.+?), CC", credits)
    for rel in ("index.html", "en/index.html"):
        block = parse(rel).has_class("photo-credits")
        check(block, f"{rel}: .photo-credits missing")
        for artist in artists:
            check(artist in block[0]["text"], f"{rel}: credit for {artist} missing")


def test_robots_sitemap():
    check("Sitemap: https://foab.rs/sitemap.xml" in load("robots.txt"), "robots.txt must reference the sitemap")
    sm = load("sitemap.xml")
    for url in ("https://foab.rs/", "https://foab.rs/en/"):
        check(f"<loc>{url}</loc>" in sm, f"sitemap missing {url}")
        check(f'hreflang="sr" href="https://foab.rs/"' in sm and f'hreflang="en" href="https://foab.rs/en/"' in sm, "sitemap alternates")
    import xml.dom.minidom
    xml.dom.minidom.parseString(sm)  # must be well-formed


def _luminance(hex_color):
    rgb = [int(hex_color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def css_var(name):
    m = re.search(rf"--{name}:\s*(#[0-9a-fA-F]{{6}})", load("css/style.css"))
    check(m, f"--{name} not defined as a 6-digit hex")
    return m.group(1)


def test_dark_kicker_contrast():
    # Small bold kicker text on sand/white must meet WCAG AA (4.5:1).
    for bg in ("sand", "white"):
        ratio = contrast(css_var("yellow-dark"), css_var(bg))
        check(ratio >= 4.5, f"--yellow-dark on --{bg} is {ratio:.2f}:1, needs 4.5:1")


def test_form_anchor_clears_sticky_header():
    css = load("css/style.css")
    check(re.search(r"#upit[^{]*\{[^}]*scroll-margin-top", css), "#upit needs scroll-margin-top (sticky header covers it)")


def test_no_unconfirmed_claims():
    for rel in ("index.html", "en/index.html"):
        low = load(rel).lower()
        for claim in ("hitn", "emergency"):
            check(claim not in low, f"{rel}: unconfirmed claim {claim!r}")


def test_forklift_photo_alt_matches_photo():
    # The placeholder shows forklifts being driven, not repaired.
    for rel in ("index.html", "en/index.html"):
        img = parse(rel).find("img", src="/img/service-forklift.webp")
        alt = img["attrs"]["alt"].lower()
        check("popravlja" not in alt and "repair" not in alt, f"{rel}: alt {alt!r} describes a repair the photo doesn't show")


def test_js_class_set_before_paint():
    # Avoid the phone menu flashing open: html.js must be set by an inline head script, before the stylesheet.
    for rel in ("index.html", "en/index.html"):
        head = load(rel).split("</head>")[0]
        inline = re.search(r"<script>[^<]*classList\.add\(['\"]js['\"]\)[^<]*</script>", head)
        check(inline, f"{rel}: inline html.js script missing in <head>")
        check(inline.start() < head.index('rel="stylesheet"'), f"{rel}: html.js script must come before the stylesheet")


def test_photo_credits_licence_links():
    for rel in ("index.html", "en/index.html"):
        src = load(rel)
        block = src[src.index('class="photo-credits"'):]
        block = block[:block.index("</p>")]
        for lic in ("by-sa/3.0", "by-sa/4.0", "by/2.0"):
            check(f"https://creativecommons.org/licenses/{lic}/" in block, f"{rel}: credits must link licence {lic}")
        check(("izmenjen" in block) if rel == "index.html" else ("modified" in block or "cropped" in block),
              f"{rel}: credits must say the photos were modified (cropped/resized)")


def test_working_hours():
    for rel, text in (("index.html", "Radno vreme: 8–18 h"), ("en/index.html", "Working hours: 8:00–18:00")):
        src = load(rel)
        check(text in src, f"{rel}: working hours {text!r} missing")
        check("TODO(owner): add working hours" not in src, f"{rel}: stale working-hours TODO")


HCAPTCHA_SITEKEY = "50b2fe65-b00b-4b9e-ad62-3ba471098be2"  # Web3Forms' shared free-plan key


def test_form_has_hcaptcha():
    for rel, lang in (("index.html", "sr"), ("en/index.html", "en")):
        d = parse(rel)
        widget = d.has_class("h-captcha")
        check(widget, f"{rel}: hCaptcha widget missing")
        check(widget[0]["attrs"].get("data-sitekey") == HCAPTCHA_SITEKEY, f"{rel}: wrong hCaptcha sitekey")
        src = load(rel)
        form = src[src.index('id="contact-form"'):src.index("</form>")]
        check('class="h-captcha"' in form, f"{rel}: hCaptcha widget must be inside the form")
        check(form.index('class="h-captcha"') < form.index('type="submit"'), f"{rel}: widget must come before the submit button")
        check(f'src="https://js.hcaptcha.com/1/api.js?recaptchacompat=off&amp;hl={lang}"' in src, f"{rel}: hCaptcha script (hl={lang}) missing")
        check(form_attr(d, "data-msg-captcha"), f"{rel}: data-msg-captcha missing")
        check("<noscript>" in form, f"{rel}: form needs a <noscript> note (captcha needs JS)")


def form_attr(doc, name):
    return doc.find("form", id="contact-form")["attrs"].get(name)


CITIES = {"index.html": ["Novi Sad", "Beograd", "Inđija", "Stara Pazova", "Ruma"],
          "en/index.html": ["Novi Sad", "Belgrade", "Inđija", "Stara Pazova", "Ruma"]}


def test_local_search_terms():
    for rel, cities in CITIES.items():
        d = parse(rel)
        text = d.find("main")["text"]
        for city in cities:
            check(city in text, f"{rel}: visible text should mention {city}")
    sr = parse("index.html")
    check("paletar" in sr.find("title")["text"].lower(), "SR title should mention paletari")
    check("paletar" in meta(sr, name="description").lower(), "SR description should mention paletari")


def test_jsonld_services():
    for rel in ("index.html", "en/index.html"):
        data = json.loads(parse(rel).find("script", type="application/ld+json")["text"])
        offers = data.get("makesOffer", [])
        check(len(offers) == 3, f"{rel}: makesOffer should list the 3 services")
        check(all(o["@type"] == "Offer" and o["itemOffered"]["@type"] == "Service" and o["itemOffered"]["name"] for o in offers),
              f"{rel}: each offer needs an itemOffered Service with a name")
        check(data.get("@id") == "https://foab.rs/#business", f"{rel}: stable @id missing")


def test_social_meta():
    for rel in ("index.html", "en/index.html"):
        d = parse(rel)
        check(meta(d, property="og:site_name") == "FOAB", f"{rel}: og:site_name")
        check(meta(d, property="og:image:width") == "1200" and meta(d, property="og:image:height") == "630", f"{rel}: og:image size")
        check(meta(d, property="og:image:alt"), f"{rel}: og:image:alt")
        check(meta(d, name="twitter:card") == "summary_large_image", f"{rel}: twitter:card")


def test_internal_files_not_published():
    cfg = load("_config.yml")
    for item in ("README.md", "CLAUDE.md", "docs", "tests", "tools"):
        check(re.search(rf"^\s*-\s*{re.escape(item)}\s*$", cfg, re.M), f"_config.yml must exclude {item}")


def test_root_favicon_ico():
    from PIL import Image
    with Image.open(path("favicon.ico")) as im:
        check(im.format == "ICO", "favicon.ico is not an ICO file")
        check((32, 32) in im.info.get("sizes", set()), "favicon.ico should include 32x32")


def test_404_page():
    d = parse("404.html")
    check(meta(d, name="robots") == "noindex", "404 must be noindex")
    check(d.find("a", href="/") and d.find("a", href="/en/"), "404 must link to both homepages")
    check(d.find("a", href=TEL), "404 must offer the phone number")
    for el in d.elements:
        for attr in ("src", "href"):
            url = el["attrs"].get(attr, "")
            if url and not url.startswith(("/", "http", "mailto:", "tel:", "#")):
                raise AssertionError(f"404.html: relative {attr}={url} breaks on nested URLs")


def test_assets_resolve():
    for rel in HTML_PAGES:
        d = parse(rel)
        for el in d.elements:
            for attr in ("src", "href"):
                url = el["attrs"].get(attr, "")
                if not url or url.startswith(("http", "mailto:", "tel:", "#", "data:")):
                    continue
                target = url.split("#")[0]
                if not target:
                    continue
                fs = path(target.lstrip("/")) if target.startswith("/") else os.path.join(os.path.dirname(path(rel)), target)
                if fs.endswith("/") or os.path.isdir(fs):
                    fs = os.path.join(fs, "index.html")
                check(os.path.exists(fs), f"{rel}: {attr}={url} does not resolve")


def main():
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok    {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
