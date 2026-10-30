# FOAB website (foab.rs)

The website for FOAB, a family forklift repair company. It's plain HTML, CSS and JavaScript, so there's no build step and no npm. It comes in two languages: Serbian at `/` and English at `/en/`.

## Preview locally

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

The Google Map stays blank when previewing locally. Its API key only works on foab.rs.

## Run the checks

```bash
python3 tests/check_site.py                       # markup, links, assets, SR/EN parity
tests/run_browser.sh tests/js.test.html           # menu, language switch, contact form
BUDGET=60000 tests/run_browser.sh tests/overflow.html   # no sideways scrolling at 320–1280px
```

The browser tests need Chromium (`chromium` on the PATH, or set `CHROME=/path/to/chrome`).

## Going live (one-time)

The live site still serves the old Angular build from the `gh-pages` branch until you switch it:

1. Merge this work into `master`.
2. Go to GitHub → repository **Settings → Pages**. Set **Source** to "Deploy from a branch", choose branch `master` and folder `/ (root)`, then save.
3. On the same page, check that the custom domain is `foab.rs` and turn on **Enforce HTTPS**. The `CNAME` file in the repo keeps the domain set from now on.
4. When the new site is live, you can delete the old `gh-pages` branch.

After that, every push to `master` updates the site within a minute or two.

## Contact form setup (Web3Forms)

The form sends messages to **foab.nesa@gmail.com** through [Web3Forms](https://web3forms.com), which is free for up to 250 messages a month.

1. Go to https://web3forms.com, enter `foab.nesa@gmail.com` and create an access key. The key arrives by email.
2. In **both** `index.html` and `en/index.html`, replace `YOUR_WEB3FORMS_ACCESS_KEY` with the key.
3. Commit, push, and send a test message from the live site.

The key is meant to be public, so it's fine for it to be in the HTML.

## Google Maps key

The map uses the Maps Embed API, which is free. Its key is visible in the HTML, so it should only work on your domain. In Google Cloud Console → **APIs & Services → Credentials**, open the key and set:

- **Application restrictions:** Websites, with `foab.rs/*` and `*.foab.rs/*`
- **API restrictions:** Maps Embed API only

It already looks restricted, because it refuses requests from `localhost`. Check that `foab.rs` is on the list.

## Swapping in real photos

The photos in `img/` are temporary placeholders from Wikimedia Commons. To replace one:

1. Save your photo **under the same file name**: `hero.webp`, `service-forklift.webp`, `service-rental.webp`, `service-tractor.webp` or `about.webp`.
   - Hero: 1920×1080. Cards: 800×533. About: 1000×750.
   - Keep each file under about 200 KB. Any image editor can export WebP; https://squoosh.app works in the browser.
2. Remove that photo's credit from the footer of both pages and from `img/CREDITS.md`.

## Still to fill in

Search for `TODO(owner)` in `index.html` and `en/index.html`. Change both languages each time:

- [ ] Web3Forms access key (see above)
- [ ] Working hours (Kontakt section)
- [ ] Forklift types and brands you service (forklift repair card)
- [ ] The family story (O nama section)
- [ ] Real photos, and removing the placeholder credits

## Layout of the repo

| Path | What it is |
|---|---|
| `index.html`, `en/index.html` | The two language versions of the page |
| `hvala.html`, `en/thank-you.html` | Thank-you pages for when JavaScript is off |
| `css/style.css` | All styles |
| `js/main.js` | Mobile menu, language switch, contact form |
| `img/brand/` | Logo, favicon, share image (made by `tools/export_brand.py`) |
| `tests/` | Automated checks |
| `docs/superpowers/` | Design spec and implementation plan |
