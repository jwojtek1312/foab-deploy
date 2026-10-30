// FOAB site behaviour: mobile nav, language switch, contact form.
// Every feature degrades gracefully: without JS the nav stays visible and the form posts normally.

export function initNav(root = document) {
  root.documentElement.classList.add("js");
  const header = root.querySelector(".site-header");
  const toggle = root.querySelector(".nav-toggle");
  const nav = root.getElementById("site-nav");
  if (!header || !toggle || !nav) return;

  const setOpen = (open) => {
    header.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", String(open));
  };

  toggle.addEventListener("click", () => setOpen(!header.classList.contains("open")));
  nav.addEventListener("click", (e) => {
    if (e.target.closest("a")) setOpen(false);
  });
  root.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && header.classList.contains("open")) {
      setOpen(false);
      toggle.focus();
    }
  });
}

// Keep the reader on the same section when switching language (section ids match across pages).
export function initLangSwitch(root = document) {
  const link = root.querySelector(".lang-switch");
  if (!link) return;
  link.addEventListener("click", () => {
    const base = link.getAttribute("href").split("#")[0];
    link.setAttribute("href", base + (location.hash || ""));
  });
}

// Submit to Web3Forms in the background; messages come from the form's data-msg-* attributes,
// so this file has no language-specific text.
export function initForm(form, fetchImpl = (...args) => fetch(...args)) {
  if (!form) return;
  const button = form.querySelector('button[type="submit"], button:not([type])');
  const status = form.querySelector(".form-status");
  let sending = false;

  const show = (key, cls) => {
    if (!status) return;
    status.textContent = form.dataset[key] || "";
    status.classList.remove("is-success", "is-error");
    if (cls) status.classList.add(cls);
  };

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (sending) return;
    sending = true;
    if (button) button.disabled = true;
    show("msgSending");

    const body = new FormData(form);
    body.delete("redirect"); // only used by the no-JS fallback

    try {
      const res = await fetchImpl(form.action, {
        method: "POST",
        headers: { Accept: "application/json" },
        body,
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.message || "Submit failed");
      form.reset();
      show("msgSuccess", "is-success");
    } catch (err) {
      console.error("Contact form:", err);
      show("msgError", "is-error");
    } finally {
      sending = false;
      if (button) button.disabled = false;
    }
  });
}

function highlightActiveSection(root = document) {
  const links = [...root.querySelectorAll('#site-nav a[href^="#"]')];
  if (!links.length || !("IntersectionObserver" in window)) return;
  const byId = new Map(links.map((a) => [a.getAttribute("href").slice(1), a]));
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        links.forEach((a) => a.classList.remove("active"));
        byId.get(entry.target.id)?.classList.add("active");
      }
    },
    { rootMargin: "-45% 0px -50% 0px" },
  );
  byId.forEach((_, id) => {
    const section = root.getElementById(id);
    if (section) observer.observe(section);
  });
}

function init() {
  if (!document.querySelector(".site-header")?.hasAttribute("data-site")) return;
  initNav(document);
  initLangSwitch(document);
  initForm(document.getElementById("contact-form"));
  highlightActiveSection(document);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
