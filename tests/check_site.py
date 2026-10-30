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
