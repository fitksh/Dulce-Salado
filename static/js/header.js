(function () {
  "use strict";
  document.documentElement.dataset.inputModality = "pointer";
  document.addEventListener("pointerdown", () => { document.documentElement.dataset.inputModality = "pointer"; }, { passive: true });
  document.addEventListener("keydown", event => { if (event.key === "Tab") document.documentElement.dataset.inputModality = "keyboard"; });
  const panels = [...document.querySelectorAll("[data-header-panel]")];
  function positionLocation(panel) {
    if (panel.id !== "ubicacion" || !panel.open) return;
    const content = panel.querySelector(".location-details");
    const trigger = panel.querySelector("summary").getBoundingClientRect();
    const parent = content.offsetParent.getBoundingClientRect();
    const width = content.getBoundingClientRect().width;
    const center = Math.max(16 + width / 2, Math.min((trigger.left + trigger.right) / 2, window.innerWidth - 16 - width / 2));
    content.style.left = `${center - width / 2 - parent.left}px`;
    content.style.right = "auto";
  }
  const hover = window.matchMedia("(hover: hover) and (pointer: fine)");
  const closeTimers = new Map();
  function cancelClose(panel) {
    window.clearTimeout(closeTimers.get(panel));
    closeTimers.delete(panel);
  }
  function close(panel) { cancelClose(panel); panel.open = false; }
  function closeOthers(current) { panels.forEach(panel => { if (panel !== current) close(panel); }); }
  function open(panel) { cancelClose(panel); closeOthers(panel); panel.open = true; positionLocation(panel); }
  function focusInside(panel) { return panel.querySelector(".header-panel-content").contains(document.activeElement); }
  panels.forEach(panel => {
    const clickOnly = panel.hasAttribute("data-click-only");
    panel.addEventListener("toggle", () => { if (panel.open) { closeOthers(panel); positionLocation(panel); } });
    panel.addEventListener("pointerenter", event => {
      if (clickOnly || event.pointerType !== "mouse" || !hover.matches) return;
      if (panels.some(other => other !== panel && other.open && focusInside(other))) return;
      open(panel);
    });
    panel.addEventListener("pointerleave", event => {
      if (clickOnly || event.pointerType !== "mouse" || !hover.matches) return;
      cancelClose(panel);
      // Permite cruzar el espacio hasta el panel sin cerrarlo durante el recorrido.
      closeTimers.set(panel, window.setTimeout(() => {
        closeTimers.delete(panel);
        if (!panel.matches(":hover") && !focusInside(panel)) panel.open = false;
      }, 200));
    });
    panel.querySelector("summary").addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") cancelClose(panel);
    });
    panel.querySelector("summary").addEventListener("click", event => {
      if (!clickOnly && event.detail > 0 && event.pointerType !== "touch" && hover.matches) {
        event.preventDefault();
        open(panel);
      }
    });
    if (clickOnly) panel.addEventListener("click", event => {
      if (event.target.closest("a")) close(panel);
    });
    panel.addEventListener("focusout", event => {
      if (!panel.contains(event.relatedTarget) && (clickOnly || !panel.matches(":hover"))) close(panel);
    });
  });
  const mobile = window.matchMedia("(max-width: 767px)");
  const search = document.getElementById("catalog-search");
  const desktopPlaceholder = search?.placeholder;
  function updateViewport() {
    if (search) search.placeholder = mobile.matches ? "Buscar productos..." : desktopPlaceholder;
    panels.forEach(panel => {
      if (!mobile.matches && panel.hasAttribute("data-click-only")) close(panel);
      positionLocation(panel);
    });
  }
  mobile.addEventListener("change", updateViewport);
  window.addEventListener("resize", updateViewport);
  updateViewport();
  panels.forEach(positionLocation);
  document.addEventListener("click", event => {
    panels.forEach(panel => { if (!panel.contains(event.target)) close(panel); });
  });
  document.addEventListener("keydown", event => {
    if (event.key !== "Escape") return;
    const panel = panels.find(item => item.open);
    if (!panel) return;
    close(panel);
    panel.querySelector("summary").focus({ preventScroll: true });
    event.preventDefault();
  });
})();
