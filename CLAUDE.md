# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Single-page marketing site for FOAB, a machine/forklift repair business ("Popravka mašina"). User-facing text is in Serbian (Latin script). Angular 17 (standalone components, CLI 17.2) with SSR + prerendering, styled with Materialize CSS.

## Commands

- `npm start` (`ng serve`) — dev server at http://localhost:4200
- `npm run build` (`ng build`) — production build to `dist/foab-webpages/` (`browser/` + `server/`); routes are prerendered (`"prerender": true`)
- `npm run watch` — development build in watch mode
- `npm run serve:ssr:foab-webpages` — run the built Express SSR server (port 4000, override with `PORT`)
- `npm test` (`ng test`) — Karma/Jasmine unit tests (needs Chrome). Run a single spec by narrowing with `fdescribe`/`fit`, or `ng test --include src/app/app.component.spec.ts`
- `ng deploy` — deploys via `angular-cli-ghpages` (GitHub Pages)

## Architecture

- The whole site currently lives in one component: `src/app/app.component.html` (navbar, banner, feature icons, parallax sections, "O Nama"/about with Google Maps iframe, "Kontakt" form, footer). `app.routes.ts` is empty; in-page navigation uses `#anchor` links with `scroll-behavior: smooth` in `src/styles.css`.
- Styling: Materialize CSS and its JS are loaded globally through `angular.json` (`styles`/`scripts`), not imported in components. Use Materialize utility classes (`orange darken-2`, `col s12 m4`, etc.). Custom global styles go in `src/styles.css`; component CSS is subject to a 2kb warn / 4kb error production budget.
- Materialize's JS global is exposed as `M` (`declare const M: any` in `app.component.ts`, `declare module 'M'` in `src/typings.d.ts`). JS-driven widgets (parallax, sidenav) are not initialized anywhere yet — if adding initialization, guard it to run only in the browser (e.g. `afterNextRender` / `isPlatformBrowser`), since the app is server-rendered and `M`/`document` don't exist on the server.
- SSR wiring: `src/main.ts` (browser bootstrap, `app.config.ts` with router + client hydration) and `src/main.server.ts` (`app.config.server.ts` merges in `provideServerRendering`); `server.ts` is the Express entry that serves static files from `dist/.../browser` and renders everything else with `CommonEngine`.
- Static assets (images, favicons) live in `src/assets/` and are referenced as `assets/...`.

## Notes

- `src/app/app.component.spec.ts` is the unmodified CLI scaffold and its "should render title" test (expects `Hello, foab-webpages` in an `h1`) no longer matches the template.
- `taiga-ui` is listed in dependencies but not used.
