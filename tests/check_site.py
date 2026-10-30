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
MAP_SRC = ("https://www.google.com/maps/embed/v1/place?key=AIzaSyBG0WZ9O3HYuaW35LKTOOWRJpnlg19hLuI"
           "&q=Cara+Du%C5%A1ana+58%2C+22324+Be%C5%A1ka%2C+Serbia")
SECTIONS = ["usluge", "o-nama", "kontakt"]
FIELDS = {"ime": True, "firma": False, "kontakt": True, "poruka": True}
HTML_PAGES = ["index.html", "hvala.html", "en/index.html", "en/thank-you.html"]


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
    check("access_key" in hidden, f"{rel}: access_key missing")
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
