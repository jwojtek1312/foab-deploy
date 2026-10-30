# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Static site for FOAB, a family forklift repair company, served at **foab.rs** from GitHub Pages (`master`, repo root; `CNAME` holds the domain). It's plain HTML, CSS and JS: no build step, no npm, no framework, no CDN libraries, no Google Fonts or icon fonts. Serbian (Latin script) is the primary language at `/`, and English is at `/en/`. The design spec and plan are in `docs/superpowers/` and explain the reasoning behind decisions.

## Commands

- `python3 -m http.server 8000`: local preview. The Google Map refuses localhost, which is expected.
- `python3 tests/check_site.py`: stdlib structural checks. These cover required markup, the form contract, SR/EN parity, local links and assets resolving, image sizes, no template or fake text, and robots/sitemap. Each `test_*` function is discovered automatically, so add new checks as functions in this file.
- `tests/run_browser.sh tests/js.test.html`: tests for `js/main.js` in headless Chromium.
- `BUDGET=60000 tests/run_browser.sh tests/overflow.html`: no horizontal overflow at 320/375/768/1280px on all four pages.
- `python3 tools/export_brand.py`: regenerates every file in `img/brand/` from the mark geometry in that script. Edit the script, never the generated SVG/PNG files.

Chromium is a snap here, so it can only read and write under `$HOME`. Scratch output goes in `.superpowers/tmp/` (git-ignored), not `/tmp`.

## How the pieces fit

- **The two pages are hand-maintained copies of each other.** `index.html` and `en/index.html` have the same structure, section ids (`#usluge`, `#o-nama`, `#kontakt`, `#upit`), form field names (`ime`, `firma`, `kontakt`, `poruka`) and number of `tel:` links. `test_en_parity` enforces this. Any change to one page must be made to the other. The same applies to `hvala.html` and `en/thank-you.html`.
- **The language switch** (`.lang-switch`) is a plain link to the other page. JS appends the current `#hash`, which is why section ids are shared across languages.
- **`js/main.js` is an ES module** that exports `initNav`, `initLangSwitch` and `initForm`.
  - It only auto-initialises when the header has a `data-site` attribute, so the test fixture can import it without double-binding.
  - It contains no user-facing text. Form messages come from the form's `data-msg-sending`, `data-msg-success` and `data-msg-error` attributes.
- **The contact form** posts to Web3Forms (`https://api.web3forms.com/submit`).
  - With JS, `initForm` submits via `fetch`, drops the `redirect` field, disables the button while sending, and shows a message in `.form-status`. On error it keeps whatever the user typed.
  - Without JS, it is a normal POST that redirects to the thank-you page.
  - The access key placeholder is `YOUR_WEB3FORMS_ACCESS_KEY`.
- **Progressive enhancement:** CSS only hides the phone menu under `html.js`, a class `initNav` adds, so the nav stays usable without JS.
- **Phones (`max-width: 767px`)** get a fixed yellow `.call-bar` (`tel:` link), and `body` has a matching `padding-bottom` so the bar never covers content.
- **The style is "bold and industrial":** black `#111111`, yellow `#F5B91B`, sand `#f4f3ef`, and hazard-stripe dividers (`--stripes`). Yellow is never used as text on a light background. Use `--yellow-dark` there instead.

## Content rules

- **Never show invented data.** That includes made-up hours, numbers, client counts, years, or "short/long-term" style claims. Unknowns are marked `<!-- TODO(owner): … -->` and use neutral wording that is true. The README lists the open TODOs.
- **Fixed contact details:**
  - Phone: `tel:+381641196048`, displayed as `064 119 6048` (SR) and `+381 64 119 6048` (EN).
  - Email: `foab.nesa@gmail.com`.
  - Workshop: `Cara Dušana 58, 22324 Beška`. FOAB serves customers on-site anywhere in Serbia, so the map is labelled as the workshop rather than as a place to visit.
- **Placeholder photos are Wikimedia Commons CC BY / BY-SA.** While a placeholder is in use, it must stay credited both in the footer `.photo-credits` of both pages and in `img/CREDITS.md`. `test_photo_credits_visible` checks this. When a real photo replaces one, remove its credit in all three places.
- **Images:** WebP, ≤ 200 KB, stable file names (`img/hero.webp` etc.), and every `<img>` has `alt`, `width` and `height`.
