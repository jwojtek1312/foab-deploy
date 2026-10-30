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

The form sends messages to **foab.nesa@gmail.com** through [Web3Forms](https://web3forms.com), which is free for up to 250 messages a month. The access key is already in the `access_key` field of both `index.html` and `en/index.html`. The key is meant to be public, so it's fine for it to be in the HTML.

After going live, send a test message from the site in each language and check that it arrives. To change the recipient, create a new key at web3forms.com and replace it in both pages.

**Spam protection:** hCaptcha is turned on in the Web3Forms dashboard. With it on, Web3Forms rejects any message that doesn't include a solved captcha, including bots that post straight to the API with the public key. The widget uses Web3Forms' free shared site key, loaded straight from hCaptcha. If you ever turn hCaptcha off in the dashboard, also remove the `h-captcha` div and the hCaptcha `<script>` from both pages. If you leave the widget in, visitors still have to solve a captcha that does nothing.

## Google Maps key

The map uses the Maps Embed API, which is free. Its key is visible in the HTML, so it should only work on your domain. In Google Cloud Console → **APIs & Services → Credentials**, open the key and set:

- **Application restrictions:** Websites, with `foab.rs/*` and `*.foab.rs/*`
- **API restrictions:** Maps Embed API only

The current key is restricted to foab.rs. That's why the map is blank in a local preview.

## Search engines

The pages already describe FOAB and its three services in a format search engines read. `sitemap.xml` and `robots.txt` are in place, and `_config.yml` stops GitHub Pages from publishing this README and the other internal files. What's left happens outside the code:

1. **Google Search Console** (https://search.google.com/search-console): add the domain `foab.rs`, verify it with the DNS TXT record Google gives you, then go to **Sitemaps** and submit `https://foab.rs/sitemap.xml`.
2. **Google Business Profile** (https://business.google.com): this is what puts FOAB on Google Maps and in local search results. Set it up as a service-area business covering Serbia, add the phone number and `https://foab.rs`, and ask longtime clients for reviews. Once the profile exists, add its link to `sameAs` in the business details block (the `application/ld+json` script) of both pages.
3. **Bing Webmaster Tools** (optional): it can import everything from Search Console in one click.

## Swapping in real photos

The photos in `img/` are temporary placeholders from Wikimedia Commons. To replace one:

1. Save your photo **under the same file name**: `hero.webp`, `service-forklift.webp`, `service-rental.webp`, `service-tractor.webp` or `about.webp`.
   - Hero: 1920×1080. Cards: 800×533. About: 1000×750.
   - Keep each file under about 200 KB. Any image editor can export WebP; https://squoosh.app works in the browser.
2. Remove that photo's credit from the footer of both pages and from `img/CREDITS.md`.

## Still to fill in

Search for `TODO(owner)` in `index.html` and `en/index.html`. Change both languages each time:

- [ ] Working days (hours are shown as 8–18 h; add the days once the family confirms)
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
