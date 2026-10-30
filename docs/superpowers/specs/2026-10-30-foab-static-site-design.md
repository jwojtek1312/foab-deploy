# FOAB website: static rebuild design

Date: 2026-10-30
Status: approved 2026-10-30

## Intent

FOAB is a small family-owned company with 15+ years of experience. It repairs forklifts and also rents forklifts and repairs tractors and hydraulics. Most clients are industrial companies with medium-to-large warehouses (standard forklifts, pallet trucks). Most business comes through phone calls and word-of-mouth. Clients tend to be old-school and call, but some managers prefer to leave a written inquiry.

The site's job, in the owner's son's words: *"hey, this is who we are, if you have a problem with your forklift, here's how you can find/contact us."* It is a trust-and-contact page, not a catalogue or a shop.

The current site (Angular 17 + SSR + Materialize, on GitHub Pages at `foab.rs`) was never finished. Its contact form has no backend, and it still has template text in it. Angular was chosen only for the form and the map, and neither needs it. This rebuild replaces it with plain HTML/CSS/JS.

## Goals

- A visitor understands in a few seconds what FOAB does, that it's an experienced family business, and that it **comes to the customer's site anywhere in Serbia**.
- Calling is the easiest action everywhere on the page. Sending a written inquiry is the second option.
- The contact form actually delivers messages to **foab.nesa@gmail.com**.
- The location is shown on a Google Map.
- Serbian and English.
- Works well and looks good on phones.
- Looks finished on day one with placeholder photos, and real photos can be swapped in later with no code changes.
- Hosting costs nothing beyond the `foab.rs` domain.

## Non-goals

- No build step, framework, npm, or bundler.
- No CMS, admin panel, blog, price list, or online booking.
- No analytics or cookie banner for now.
- No backend of our own.

## Anti-goals (failure even if it "works")

- Looks like a generic template, or still contains template or lorem text.
- The phone number is hard to find, or isn't one tap to call on a phone.
- Feels flashy or "startup-y". It should feel solid, industrial, and trustworthy.
- Implies customers must drive to the workshop. FOAB goes to them.
- Breaks or overflows horizontally on a phone (the old map iframe did).

## Constraints

- Hosted as static files. **GitHub Pages** (current) stays the default host. See "Hosting" below.
- The custom domain `foab.rs` must keep working.
- Any image or font used must be free to use commercially.
- Serbian is the primary language. It uses **Latin script**, as the current site does.

## Contact details (supplied)

- Phone: **+381 64 119 6048**. Use `tel:+381641196048`, and display it as `064 119 6048` on the Serbian page and `+381 64 119 6048` on the English page.
- Email: **foab.nesa@gmail.com**.
- Workshop address: **Cara Dušana 58, 22324 Beška, Srbija** (English page: "Cara Dušana 58, 22324 Beška, Serbia"). *(My call: I filled in the postal code 22324 for Beška. Verify it.)*

## Launch

- The new site is built and previewed locally first. The live `foab.rs` keeps serving the old `gh-pages` build until the owner switches the GitHub Pages source to `master`. That switch is the go-live moment, and the owner decides when.
- Until the Web3Forms key exists, the form is built with a marked placeholder key. The builder also gives the owner step-by-step instructions for creating the key.

## Decisions

### Stack and repo

- Plain HTML + CSS + a small amount of vanilla JS, served as-is.
- It replaces the Angular app in this same repo, on a new branch off an up-to-date `origin/master`. Note that local `master` is stale and must be pulled first. All Angular files are removed (`angular.json`, `package*.json`, `tsconfig*`, `server.ts`, `src/`, `.angular/`, `.vscode/` Angular tasks, `node_modules/`, `dist/`).
- `.superpowers/` is added to `.gitignore`.
- `CLAUDE.md` is rewritten to describe the new site.

### Hosting

- GitHub Pages, set to "Deploy from a branch" (`master`, root). This replaces the `gh-pages` branch that `ng deploy` used, and that branch becomes obsolete.
- A `CNAME` file containing `foab.rs` is committed in the repo root, so the domain no longer gets wiped on every deploy.
- Switching the Pages source in GitHub settings is a manual step for the owner. The builder documents it.
- Moving to Cloudflare Pages later (also free) needs no code changes.

### Visual direction ("A: bold and industrial", chosen in mockups)

- Colors from the logo: black `#111111` and safety yellow `#F5B91B`, plus a warm light neutral (around `#f4f3ef`) and white for light sections.
- A yellow/black diagonal hazard-stripe band is used as a divider under the header and above the contact section.
- The page alternates dark and light sections: dark hero, light services, white about, dark contact. *(My call: this borrows the calm of the "light and clean" option the owner also liked, so the page isn't heavy.)*
- Yellow is used as a fill, for borders, and for text on black. It is never used for text on white, because the contrast is too low.
- The reference mockup is `.superpowers/brainstorm/*/content/full-page.html`. It is not committed, so the summary below is the source of truth.

### Page structure (single page; one per language)

1. **Header.** Sticky and black. It holds the logo, anchor links (Usluge / O nama / Kontakt), the SR|EN switch, and a yellow phone button showing the number. On phones the links collapse into a hamburger menu.
2. **Hero.** Black. Kicker: "Porodična firma · 15+ godina". The headline leads with on-site service anywhere in Serbia (e.g. "Servis viljuškara na vašoj lokaciji, širom Srbije"). One line lists all services. There are two buttons: **Pozovite** (`tel:`) and **Pošaljite upit** (scrolls to the form).
3. **Usluge.** Three cards, and forklift repair is visually the largest.
   - *Servis viljuškara*: on-site repair, maintenance, and diagnostics for standard forklifts and pallet trucks. **For major repairs, FOAB picks up the forklift, repairs it in the workshop, and returns it.**
   - *Iznajmljivanje viljuškara*.
   - *Popravka traktora i hidraulike*.
   - Each card has a photo slot.
4. **O nama.** A short family story with a photo slot (owner or workshop) and three fact blocks: **15+ godina iskustva**, **Cela Srbija** (we come to you), and **Transport** for larger repairs. *(My call: these replace the placeholder "?? happy clients" stats from the mockup. They need no numbers we don't have.)*
5. **Kontakt.** Black, headed "Imate problem sa viljuškarom?".
   - Left column: large phone number (`tel:`), email (`mailto:`), workshop address, working hours, a line saying FOAB covers all of Serbia, and a short note that calling is fastest.
   - Right column: the form.
6. **Map.** A full-width, responsive Google Map of the **workshop**, labelled as the workshop ("Radionica"), so visitors don't assume they must come in.
7. **Footer.** Logo, © year, and phone and email again.

On phones (below ~768px), a yellow **"☎ Pozovite"** bar stays pinned to the bottom of the screen and calls in one tap.

### Languages

- Serbian at `/` (`index.html`) and English at `/en/` (`en/index.html`): two static pages that share one CSS and one JS file. *(My call: this works without JS, has no text flash, and lets search engines index both. The duplicated markup is acceptable for one page.)*
- The SR|EN switch is a plain link to the other page, preserving the current `#section` anchor.
- Each page has `lang`, `hreflang` alternates, and a translated `<title>` and meta description.
- The builder writes the English copy as a natural translation of the Serbian, not word-for-word.

### Contact form (Web3Forms)

- Posts to Web3Forms. Submissions go to foab.nesa@gmail.com.
- Fields: Ime (required), Firma (optional), Telefon ili email (required; one free-text field, because clients often prefer phone), Poruka (required). It also has Web3Forms' hidden honeypot field (`botcheck`) and a subject line such as "Novi upit sa sajta foab.rs".
- With JS: submit via `fetch`, show an inline success or error message in the page's language, and disable the button while sending. Without JS: a normal form POST with a `redirect` to a simple thank-you page per language.
- The Web3Forms access key is public by design and lives in the HTML. **The owner must create it** at web3forms.com using foab.nesa@gmail.com. Until then, a clearly marked placeholder is used.

### Google Map

- A Maps Embed API `<iframe>`, lazy-loaded and responsive (full width, fixed aspect, no fixed pixel width).
- It reuses the existing API key. The owner should restrict it in Google Cloud Console to HTTP referrers `foab.rs/*` and `*.foab.rs/*`. The builder documents this.
- The query is the workshop address: `Cara Dušana 58, Beška` (Beška, Inđija municipality, Srem). It uses the Maps Embed API `place` mode with the address as `q`. No geocoding call is needed.

### Logo and icons

The ChatGPT logo pack (`/home/nebojsa/foab-sajt/foab-logo-pack/`) is the starting point. It needs cleanup before use:

- "FOAB" overlaps the gear ring. Resize or reposition the text so it sits inside the ring.
- The text uses the system font "Arial Black", so it looks different on each machine. Convert it to outlined paths so it is identical everywhere.
- `foab-icon.svg` has a 1000×1000 viewBox but its content ends around y=640. Recenter or crop it.
- Make a **favicon without text** (gear + forks only), since "FOAB" is unreadable at 16–32px.
- Export the needed sizes: SVG favicon, a 32px PNG/ICO fallback, a 180px apple-touch-icon, and a header logo variant that reads well on black (white or yellow gear and lettering).

### Images

- Placeholder photos are free stock images (Unsplash/Pexels or similar, commercial use allowed) of forklifts, warehouses, and workshop or hydraulics work. They are stored locally and not hot-linked.
- Each photo slot gets a stable file name (e.g. `img/hero.webp`, `img/service-forklift.webp`, `img/service-rental.webp`, `img/service-tractor.webp`, `img/about.webp`). Swapping in real photos is then just replacing a file.
- Images are compressed and sized for their slot (WebP, roughly ≤200 KB each), with `width`/`height` set and `loading="lazy"` below the fold.
- Credits are kept in a small `img/CREDITS.md`.

### SEO / sharing basics

- Title and meta description per language.
- Open Graph tags with a share image.
- `LocalBusiness` JSON-LD with name, phone, email, address, and area served (Serbia).
- `sitemap.xml` and `robots.txt`.

### Placeholder content (owner to supply)

These must be easy to find and replace. Each is marked with a consistent `TODO` comment in the HTML, and a list in `CLAUDE.md` or the README:

- Working hours.
- Founding year, if they want to show it.
- Forklift types/brands serviced (electric / diesel / gas, specific brands).
- The family story for O nama.
- Web3Forms access key.
- Real photos.

Until then, visible copy uses neutral wording that is true without those details. Fake numbers are never displayed (e.g. no made-up phone number).

## Left to the builder

- Exact copy within the direction above (Serbian and English), and exact type scale, spacing, and breakpoints.
- Font choice: a system font stack, or at most one self-hosted webfont family (e.g. a sturdy grotesk for headings). No Google Fonts hot-linking.
- Icon approach (inline SVG preferred, no icon font).
- Hamburger menu implementation, smooth scrolling, and the active-section highlight.
- Choice of the specific stock photos.

## Verification

- Manual check in a browser at phone (~375px), tablet, and desktop widths, in both languages. Check that the page never scrolls horizontally.
- HTML validates (W3C validator).
- Lighthouse: no accessibility errors, and good performance on mobile.
- A test form submission arrives at foab.nesa@gmail.com once the real key exists.
- `tel:` and `mailto:` links work on a phone.
