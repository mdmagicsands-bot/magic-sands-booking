(() => {
  const root = document.querySelector("[data-legal-page]");
  if (!root) return;

  const tabs = Array.from(root.querySelectorAll("[data-legal-tab]"));
  const panels = Array.from(root.querySelectorAll("[data-legal-panel]"));

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const id = tab.dataset.legalTab;
      tabs.forEach((t) => {
        const active = t === tab;
        t.classList.toggle("is-active", active);
        t.setAttribute("aria-selected", active ? "true" : "false");
      });
      panels.forEach((panel) => {
        const active = panel.dataset.legalPanel === id;
        panel.classList.toggle("is-active", active);
        panel.hidden = !active;
      });
    });
  });

  root.querySelectorAll("[data-legal-section]").forEach((section) => {
    const toggle = section.querySelector(".legal-section-toggle");
    const body = section.querySelector(".legal-section-body");
    if (!toggle || !body) return;

    toggle.addEventListener("click", () => {
      const open = !section.classList.contains("is-open");
      section.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      body.hidden = !open;
    });
  });
})();
