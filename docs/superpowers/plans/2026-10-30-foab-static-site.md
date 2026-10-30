# FOAB Static Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the unfinished Angular site with a bilingual (SR/EN), mobile-friendly static site for FOAB. It needs a working Web3Forms contact form and a Google Map, and is served from GitHub Pages.

**Architecture:** Two static HTML pages (`/index.html` Serbian and `/en/index.html` English) plus two thank-you pages. They share one stylesheet and one ES-module script. There is no build step. Tests are a stdlib Python checker for markup and assets, plus browser-run HTML test pages for JS behavior and layout overflow. Both run against `python3 -m http.server` with headless Chromium.

**Tech Stack:** HTML5, CSS (custom properties, grid, `clamp()`), vanilla JS (ES modules), Web3Forms, Google Maps Embed API, Python 3 + Pillow (asset export and checks), headless Chromium (`/snap/bin/chromium`).

**Spec:** `docs/superpowers/specs/2026-10-30-foab-static-site-design.md`

## Global Constraints

- No npm, bundler, framework, CDN libraries, Google Fonts or icon fonts. Use a system font stack and inline SVG icons.
- Colors: black `#111111`, yellow `#F5B91B`, light neutral `#f4f3ef`, white. Yellow is never used for text on a light background.
- Serbian copy is in Latin script, with correct diacritics (č ć š ž đ).
- Phone: `tel:+381641196048`. Display `064 119 6048` (SR) or `+381 64 119 6048` (EN).
- Email: `foab.nesa@gmail.com`. Address: `Cara Dušana 58, 22324 Beška, Srbija` (EN: `…, Serbia`).
- No fake data is ever shown. Unknowns (working hours, founding year, forklift types/brands, family story, Web3Forms key, real photos) are marked `<!-- TODO(owner): … -->` and use neutral, true copy.
- Web3Forms endpoint `https://api.web3forms.com/submit`. Placeholder key is `YOUR_WEB3FORMS_ACCESS_KEY`.
- Maps embed: `https://www.google.com/maps/embed/v1/place?key=AIzaSyBG0WZ9O3HYuaW35LKTOOWRJpnlg19hLuI&q=Cara+Du%C5%A1ana+58%2C+22324+Be%C5%A1ka%2C+Serbia`
- Phone breakpoint: `max-width: 767px` (sticky call bar and hamburger menu).
- Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **A 320px-wide phone with long Serbian words** ("Iznajmljivanje", "viljuškara") must not scroll the page horizontally. Owned by Task 6, which runs the overflow test at 320, 375, 768, and 1280px for both languages.
2. **A form submit that fails** (offline, Web3Forms error, or the placeholder key) must show the error message in the page's language. The button must be re-enabled and the typed text kept. Owned by Task 4: `test_submit_error_keeps_input`.
3. **Double-clicking Send** must produce only one request, because the button is disabled while sending. Owned by Task 4: `test_no_double_submit`.
4. **With JS disabled**, the form must still post and redirect to the thank-you page, and every nav link must still be reachable. Owned by Task 3 (checker asserts `action`, `method`, and `redirect`) and Task 4 (no-JS nav: links are visible unless `html.js` is set).
5. **On phones, the sticky call bar must not cover** the form's submit button or the footer. Owned by Task 3: the checker asserts the bottom padding rule. Task 6 checks it in a screenshot.

---

## File Structure

```
index.html              Serbian page
en/index.html           English page
hvala.html              SR thank-you (no-JS form redirect)
en/thank-you.html       EN thank-you
css/style.css           all styles
js/main.js              ES module: nav, form, lang switch
img/                    hero.webp service-forklift.webp service-rental.webp service-tractor.webp about.webp CREDITS.md
img/brand/              logo-light.svg (for dark bg) logo.svg icon.svg favicon.svg favicon-32.png apple-touch-icon.png og-image.png
tools/export_brand.py   renders PNG icons from SVG (Pillow + headless Chromium)
tests/check_site.py     stdlib structural checks (run: python3 tests/check_site.py)
tests/js.test.html      browser tests for js/main.js
tests/overflow.html     loads each page in iframes at fixed widths, reports overflow
tests/run_browser.sh    serves the repo, runs a test page in headless Chromium, prints result
CNAME robots.txt sitemap.xml README.md CLAUDE.md .gitignore
```

Test pages write their result into `<pre id="result">` as `PASS n` or `FAIL: …` lines. `tests/run_browser.sh <page>` greps the dumped DOM and exits non-zero on any `FAIL`.

---

### Task 1: Clean repo and add test harness

**Files:**
- Delete: `angular.json package.json package-lock.json tsconfig*.json server.ts src/ .vscode/ .editorconfig` (and untracked `node_modules/ dist/ .angular/`)
- Create: `.gitignore`, `CNAME`, `tests/check_site.py`, `tests/run_browser.sh`

**Interfaces:**
- Produces: `python3 tests/check_site.py`, which runs every `test_*` function, prints `ok`/`FAIL` per test, and exits 1 on failure. Helpers `load(path) -> str` and `parse(path) -> Doc` (a stdlib `HTMLParser` collecting elements as `(tag, attrs dict, text)` with `find_all(tag, **attrs)`). Also `tests/run_browser.sh tests/<page>.html`.

- [ ] **Step 1:** `git fetch && git checkout -b static-site origin/master`.
- [ ] **Step 2:** Delete the Angular files listed above. Write `.gitignore` (`.superpowers/`, `.DS_Store`, `__pycache__/`, `*.log`) and `CNAME` containing `foab.rs`.
- [ ] **Step 3:** Write `tests/check_site.py` with the helpers and a first test, `test_cname`: the file `CNAME` stripped equals `foab.rs`. Also `test_no_angular_left`: `angular.json`, `package.json`, and `src/` don't exist.
- [ ] **Step 4:** Write `tests/run_browser.sh`. It starts `python3 -m http.server 8765` in the background, runs `chromium --headless=new --disable-gpu --virtual-time-budget=8000 --dump-dom http://localhost:8765/$1`, kills the server, prints the `#result` text, and exits 1 if it contains `FAIL` or no `PASS`. Use a trap for cleanup.
- [ ] **Step 5:** Run `python3 tests/check_site.py`. Expected: 2 ok.
- [ ] **Step 6:** Commit: "Remove Angular app; add static-site test harness".

### Task 2: Brand assets

**Files:**
- Create: `img/brand/{logo.svg,logo-light.svg,icon.svg,favicon.svg}`, `tools/export_brand.py`, generated `img/brand/{favicon-32.png,apple-touch-icon.png,og-image.png}`
- Modify: `tests/check_site.py`

**Interfaces:**
- Produces: the asset paths above, referenced by Tasks 3 and 5.

- [ ] **Step 1: Write failing tests.** Add `test_brand_svgs`. For each of the 4 SVGs: it exists, contains no `<text` element (the lettering is outlined paths), and has a `viewBox`. Add `test_brand_pngs`. Using Pillow: `favicon-32.png` is 32×32, `apple-touch-icon.png` is 180×180, `og-image.png` is 1200×630.
- [ ] **Step 2:** Run the checker. Expected: FAIL (files missing).
- [ ] **Step 3: Write the SVGs.** Start from `/home/nebojsa/foab-sajt/foab-logo-pack/foab-logo.svg`.
  - Draw "FOAB" as hand-authored `<path>` letter shapes. Use bold geometric block capitals, and the letters must fit inside the inner ring (r≈190 around 500,390) without touching it.
  - Keep the gear and the yellow forks.
  - `logo.svg`: dark ink on transparent. `logo-light.svg`: white ring, teeth, and letters, and yellow forks, for the black header.
  - `icon.svg`: the same mark, with a viewBox cropped tight to the gear (about 10px margin).
  - `favicon.svg`: gear and forks only, no letters, with thicker strokes.
- [ ] **Step 4:** Write `tools/export_brand.py`.
  - Rasterize with Chromium: `chromium --headless=new --screenshot=out.png --window-size=W,H --default-background-color=00000000 file://…` on a tiny generated HTML page that shows the SVG at that size.
  - Write `favicon-32.png` and `apple-touch-icon.png` from `favicon.svg`. The apple icon has a white background.
  - Write `og-image.png` at 1200×630: black background, `logo-light.svg` on the left, and "Servis viljuškara · širom Srbije" with the phone number on the right, drawn in the HTML page.
- [ ] **Step 5:** Run the export, then run the checker. Expected: ok. Open each PNG with the Read tool and confirm the letters don't touch the ring and the favicon reads at 32px.
- [ ] **Step 6:** Commit: "Add cleaned-up FOAB brand assets".

### Task 3: Serbian page markup and styles

**Files:**
- Create: `index.html`, `css/style.css`, `hvala.html`
- Modify: `tests/check_site.py`

**Interfaces:**
- Consumes: brand asset paths (Task 2); image paths `img/*.webp` (Task 5 supplies the files; until then they 404, which is fine).
- Produces the hooks `js/main.js` relies on:
  - `<html lang="sr">` (no `js` class, which JS adds).
  - `<header class="site-header">` with `<button class="nav-toggle" aria-controls="site-nav" aria-expanded="false">` and `<nav id="site-nav">`.
  - `<a class="lang-switch" href="/en/" hreflang="en">EN</a>`.
  - Section ids: `#usluge`, `#o-nama`, `#kontakt`.
  - `<form id="contact-form" action="https://api.web3forms.com/submit" method="POST" data-msg-sending data-msg-success data-msg-error>` containing `<p class="form-status" role="status" aria-live="polite">` and `<button type="submit">`.
  - `<a class="call-bar" href="tel:+381641196048">`.

- [ ] **Step 1: Write failing tests** in `check_site.py` for `index.html`:
  - `test_sr_basics`: `lang="sr"`, `<title>` contains "FOAB", there is a meta description, `<link rel="alternate" hreflang="en" href="https://foab.rs/en/">` and `hreflang="sr"` (self), a viewport meta, `og:title`, `og:description`, `og:image` (`https://foab.rs/img/brand/og-image.png`), a `rel="icon"` link to `/img/brand/favicon.svg`, and `rel="apple-touch-icon"`.
  - `test_sr_phone`: at least 3 `a[href="tel:+381641196048"]` (header, hero, contact, call bar), and the visible text `064 119 6048` appears.
  - `test_sr_sections`: ids `usluge`, `o-nama`, `kontakt` exist, and the nav has links `#usluge #o-nama #kontakt`.
  - `test_sr_form`: the form has the action and method above. It has hidden inputs `access_key`, `subject` (`Novi upit sa sajta foab.rs`), `from_name` (`FOAB sajt`), and `redirect` (`https://foab.rs/hvala.html`), plus a hidden checkbox `botcheck`. The visible fields named `ime` (required), `firma` (not required), `kontakt` (required), and `poruka` (required, textarea) each have a `<label for>`. All three `data-msg-*` attributes are non-empty.
  - `test_sr_map`: one iframe whose `src` equals the Global Constraints URL, with `loading="lazy"` and a `title`, and no `width` attribute.
  - `test_sr_jsonld`: a `<script type="application/ld+json">` that parses as JSON with `@type` `LocalBusiness`, `telephone` `+381641196048`, `email`, `address.streetAddress` `Cara Dušana 58`, `address.addressLocality` `Beška`, `address.postalCode` `22324`, `areaServed` `Serbia`.
  - `test_no_fake_or_template_text`: across all HTML files, none of `lorem`, `Speeds up development`, `06x`, `xxx` (case-insensitive).
  - `test_call_bar_padding`: `css/style.css` contains a `@media (max-width: 767px)` block that sets `padding-bottom` on `body`.
  - `test_hvala`: `hvala.html` has `lang="sr"`, a link to `/`, and the phone link.
- [ ] **Step 2:** Run the checker. Expected: these tests FAIL.
- [ ] **Step 3: Write `index.html`.** Follow the spec's "Page structure" in order: header, hazard stripe, hero, usluge, o-nama, stripe, kontakt, map, footer, call bar. Add `<script type="module" src="/js/main.js">`. Copy points the spec fixes:
  - Hero kicker "Porodična firma · 15+ godina".
  - Headline "Servis viljuškara na vašoj lokaciji, širom Srbije".
  - The forklift card names the pick-up/repair/return transport for major repairs.
  - The three fact blocks are "15+ godina iskustva", "Cela Srbija", and "Transport".
  - The contact heading is "Imate problem sa viljuškarom?" with the line "Najbrže je da pozovete." The map caption is "Radionica: Cara Dušana 58, Beška".
  - TODO comments go at hours, forklift types, story, access key, and each photo.
- [ ] **Step 4: Write `css/style.css`.**
  - Tokens on `:root`. Mobile-first. Sticky header.
  - `.stripes` uses `repeating-linear-gradient(-45deg, #F5B91B 0 14px, #111 14px 28px)`.
  - Services grid is 1 column on phones and `1.4fr 1fr 1fr` from 900px. The kontakt grid is 1 column, then 2 columns from 900px.
  - The map wrapper uses `aspect-ratio: 16/7` (`4/3` on phones), with the iframe at width and height 100% and no border.
  - Under 767px: hide `#site-nav` only when `html.js .site-header:not(.open)` (so it stays visible without JS), show `.nav-toggle`, show `.call-bar` fixed at the bottom, and add `body { padding-bottom: <call-bar height + 8px> }`.
  - Add a visible `:focus-visible` outline, `scroll-margin-top` on sections for the sticky header, and `prefers-reduced-motion` to turn off smooth scroll.
- [ ] **Step 5: Write `hvala.html`.** Same header and footer, plus a short "Hvala, javićemo vam se uskoro." message, a back link, and the phone number.
- [ ] **Step 6:** Run the checker. Expected: all ok.
- [ ] **Step 7:** Commit: "Add Serbian page, styles and thank-you page".

### Task 4: JavaScript (nav, form, language switch)

**Files:**
- Create: `js/main.js`, `tests/js.test.html`

**Interfaces:**
- Produces (named exports from `js/main.js`):
  - `initNav(root: Document) -> void`: adds `js` to `<html>`. The toggle flips `.open` on `.site-header` and `aria-expanded`. Clicking a nav link or pressing Escape closes the menu.
  - `initLangSwitch(root: Document) -> void`: on click, appends `location.hash` to the `.lang-switch` href.
  - `initForm(form: HTMLFormElement, fetchImpl = fetch) -> void`: intercepts submit. It POSTs `new FormData(form)` with header `Accept: application/json`, and drops `redirect` from the payload. While sending, it disables the button and shows `data-msg-sending`. On `{success:true}` it shows `data-msg-success` and resets the form. On a non-success response or a thrown error it shows `data-msg-error`, re-enables the button, and keeps the input. It sets `form-status` classes `is-success` / `is-error`.
  - The module auto-runs all three on `DOMContentLoaded` only when `document.querySelector('.site-header')` exists, so the test page can import it safely.

- [ ] **Step 1: Write `tests/js.test.html`** with a minimal fixture (header, toggle, nav, lang-switch, and a form with the data attributes and a filled `poruka`). It imports `../js/main.js` and runs these tests with a stub `fetchImpl`, writing `PASS`/`FAIL` lines to `#result`:
  - `test_nav_toggle`: the toggle click gives `.site-header.open` and `aria-expanded="true"`. A second click removes it.
  - `test_nav_escape_closes`.
  - `test_submit_success`: the stub resolves `{ok:true, json:()=>({success:true})}`. The status text equals `data-msg-success`, `poruka` is empty, and the button is enabled.
  - `test_submit_error_keeps_input`: the stub rejects. The status equals `data-msg-error`, `poruka` still has its value, and the button is enabled.
  - `test_submit_api_failure`: the stub resolves `{success:false}`, which shows the error message.
  - `test_no_double_submit`: the stub returns a never-resolving promise. Dispatching submit twice gives a call count of 1.
  - `test_redirect_not_sent`: the FormData passed to the stub has no `redirect` key.
- [ ] **Step 2:** Run `tests/run_browser.sh tests/js.test.html`. Expected: FAIL (module missing).
- [ ] **Step 3:** Implement `js/main.js` per the Interfaces above.
- [ ] **Step 4:** Run `tests/run_browser.sh tests/js.test.html`. Expected: `PASS 7`, no FAIL.
- [ ] **Step 5:** Commit: "Add nav, contact form and language switch scripts".

### Task 5: English pages and photos

**Files:**
- Create: `en/index.html`, `en/thank-you.html`, `img/*.webp`, `img/CREDITS.md`
- Modify: `tests/check_site.py`, `index.html` (only if image dimensions differ)

**Interfaces:**
- Consumes: the same hooks and classes as Task 3. Absolute paths (`/css/style.css`, `/js/main.js`, `/img/…`) work from `/en/`.

- [ ] **Step 1: Write failing tests:**
  - `test_en_parity`: `en/index.html` has `lang="en"`, the same section ids, the same form field names, the same number of `tel:` links as SR, a `redirect` of `https://foab.rs/en/thank-you.html`, the subject `New inquiry from foab.rs`, `.lang-switch` `href="/"` `hreflang="sr"`, and the display phone `+381 64 119 6048`.
  - `test_images`: each of `hero, service-forklift, service-rental, service-tractor, about` exists as `.webp` and is ≤ 200 KB. Every `<img>` in both pages has `alt`, `width`, and `height`. `img/CREDITS.md` lists every file.
  - `test_assets_resolve`: every local `src` and `href` in all 4 HTML files points to a file that exists.
- [ ] **Step 2:** Run the checker. Expected: FAIL.
- [ ] **Step 3: Write `en/index.html` and `en/thank-you.html`.** Use natural English, not literal translation. Use the section ids from SR so the language switch keeps the hash.
- [ ] **Step 4: Photos.** Download free-licence stock photos (Unsplash or Pexels) into a fresh scratch directory: a forklift in a warehouse (hero), a forklift being serviced, a rental-type forklift, a tractor or hydraulics, and a workshop.
  - Convert with Pillow to WebP at quality 80: hero 1920px wide, cards 800px, about 1000px.
  - Record the source URL, author, and licence in `CREDITS.md`.
  - If downloading is blocked, generate neutral dark gradient placeholders with Pillow at the same names and sizes, and note that in CREDITS.
- [ ] **Step 5:** Run the checker. Expected: all ok.
- [ ] **Step 6:** Commit: "Add English pages and placeholder photos".

### Task 6: Layout verification, SEO files and docs

**Files:**
- Create: `tests/overflow.html`, `robots.txt`, `sitemap.xml`, `README.md`
- Modify: `CLAUDE.md`, `tests/check_site.py`

- [ ] **Step 1: Write `tests/overflow.html`.** For each page (`/`, `/en/`, `/hvala.html`, `/en/thank-you.html`) and each width (320, 375, 768, 1280), it creates a same-origin iframe of that width. After load it asserts `doc.documentElement.scrollWidth <= width` and writes a PASS or `FAIL page@width scrollWidth=N` line.
- [ ] **Step 2:** Run `tests/run_browser.sh tests/overflow.html`. Expected: `PASS 16`. Fix the CSS for any failure.
- [ ] **Step 3: Screenshots.** Use Chromium at 375×812 and 1280×900, with `--screenshot` and full scroll height (e.g. `--window-size=375,4000`), for `/` and `/en/`. View them with Read. Check the following, and fix what fails:
  - The hero reads well.
  - Yellow text appears only on black.
  - The call bar doesn't cover the submit button.
  - The map fits the screen.
  - The menu works.
- [ ] **Step 4:** Add tests `test_robots_sitemap`: `robots.txt` references `https://foab.rs/sitemap.xml`, and `sitemap.xml` lists `https://foab.rs/` and `https://foab.rs/en/` with `xhtml:link` alternates. Write both files. Run the checker. Expected: ok.
- [ ] **Step 5: Write `README.md`** for the owner:
  - **Preview locally:** `python3 -m http.server`.
  - **Go live:** in GitHub → Settings → Pages, set Source to "Deploy from a branch", `master`, `/ (root)`. Confirm the custom domain `foab.rs` and enforce HTTPS. After that, the `gh-pages` branch can be deleted.
  - **Web3Forms key:** at web3forms.com, enter foab.nesa@gmail.com, then copy the key from the email into `access_key` in both `index.html` and `en/index.html`.
  - **Restrict the Maps key:** in Google Cloud Console → Credentials, set HTTP referrers to `foab.rs/*` and `*.foab.rs/*`.
  - **Swap photos:** replace a file in `img/`, keeping the same name.
  - **Remaining TODOs:** list each one (`grep -rn "TODO(owner)"`).
- [ ] **Step 6: Rewrite `CLAUDE.md`** for the new stack:
  - The commands: run the checker, `tests/run_browser.sh`, and the local server.
  - The page and hook structure from Task 3.
  - The rule that SR and EN pages must stay in parity, enforced by `test_en_parity`.
  - The "no fake data / TODO(owner)" rule.
- [ ] **Step 7:** Run everything: `python3 tests/check_site.py && tests/run_browser.sh tests/js.test.html && tests/run_browser.sh tests/overflow.html`. Expected: all pass.
- [ ] **Step 8:** Commit: "Add layout checks, SEO files and docs".
