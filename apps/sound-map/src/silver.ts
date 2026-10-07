// The "Sound to silver (optional)" tab: one idea at a time behind its own tab bar (WAI-ARIA tabs).
// The open idea is the `idea` URL parameter, beside main.ts's `view`; the `#` stays free for piece links.
// Old /silver#bend links redirect to ?view=silver and keep their hash, which is read once here.

const panel = document.querySelector<HTMLElement>("#silver-panel");
const bar = panel?.querySelector<HTMLElement>(".idea-tabs");
const tabs = bar ? [...bar.querySelectorAll<HTMLButtonElement>('[role="tab"]')] : [];

// Images live outside the bundle (pipeline output, else the committed demo copy), so Bun cannot resolve
// them at build time. Hidden panels keep these lazy images, and the lazy iframes, unloaded.
for (const img of panel?.querySelectorAll<HTMLImageElement>("img[data-src]") ?? []) img.src = img.dataset.src ?? "";

export function selectIdea(id: string | null, { focus = false, url: record = true } = {}) {
  if (!bar || !tabs.length) return;
  const tab = tabs.find((t) => t.dataset.tab === id) ?? tabs[0]!;
  for (const t of tabs) {
    const on = t === tab;
    t.setAttribute("aria-selected", String(on));
    t.tabIndex = on ? 0 : -1;
    document.getElementById(t.dataset.tab!)!.hidden = !on;
  }
  if (focus) tab.focus({ preventScroll: true });
  // On narrow screens the bar scrolls sideways; keep the open tab in view.
  bar.scrollTo({ left: tab.offsetLeft - bar.clientWidth / 2 + tab.clientWidth / 2 });
  const url = new URL(location.href);
  if (record && url.searchParams.get("idea") !== tab.dataset.tab) {
    url.searchParams.set("idea", tab.dataset.tab!);
    history.replaceState(null, "", url);
  }
  // Switching while scrolled down shows the new idea from its top, under the pinned bar.
  if (!panel!.hidden) {
    const top = bar.getBoundingClientRect().top + scrollY;
    if (scrollY > top) scrollTo({ top, behavior: "instant" as ScrollBehavior });
  }
}

if (bar) {
  for (const tab of tabs) tab.addEventListener("click", () => selectIdea(tab.dataset.tab!));
  bar.addEventListener("keydown", (event) => {
    const at = tabs.findIndex((t) => t.getAttribute("aria-selected") === "true");
    const to = { ArrowRight: at + 1, ArrowLeft: at - 1, Home: 0, End: tabs.length - 1 }[event.key];
    if (to === undefined) return;
    event.preventDefault();
    selectIdea(tabs[(to + tabs.length) % tabs.length]!.dataset.tab!, { focus: true });
  });
  // Links elsewhere on the page (the Installation cards) open the tab on a given idea. This runs before
  // main.ts switches the view, which keeps the `idea` parameter it finds.
  document.addEventListener("click", (event) => {
    const link = (event.target as Element).closest<HTMLElement>("[data-silver-idea]");
    if (link) selectIdea(link.dataset.silverIdea!);
  });

  const legacy = location.hash.slice(1);
  const fromHash = tabs.some((t) => t.dataset.tab === legacy) ? legacy : null;
  if (fromHash) history.replaceState(null, "", location.pathname + location.search);
  const start = new URL(location.href).searchParams;
  selectIdea(fromHash ?? start.get("idea"), { url: Boolean(fromHash) || start.get("view") === "silver" });
}
