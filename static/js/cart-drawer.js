(function () {
  "use strict";
  const dialog = document.getElementById("cart-drawer");
  if (!dialog?.showModal) return;
  const frame = dialog.querySelector("iframe"), loading = dialog.querySelector(".cart-drawer-loading");
  const target = new URL(dialog.dataset.frameUrl, window.location.href);
  document.querySelector(".cart-link")?.setAttribute("aria-haspopup", "dialog");
  document.querySelector(".cart-link")?.setAttribute("aria-controls", dialog.id);
  let opener, active = false, previousPadding;
  function finishClose() {
    if (!active) return;
    active = false;
    try {
      frame.contentDocument?.activeElement?.blur();
      frame.contentWindow?.dispatchEvent(new Event("dys-cart-panel-close"));
    } catch { /* El panel también debe cerrar si falló la carga del iframe. */ }
    frame.src = "about:blank";
    document.documentElement.classList.remove("cart-modal-open");
    document.body.style.paddingRight = previousPadding;
  }
  function restoreFocus() {
    const focus = opener?.isConnected && opener.getClientRects().length ? opener : document.querySelector(".cart-link");
    focus?.focus({ preventScroll: true });
  }
  function close() { finishClose(); if (dialog.open) dialog.close(); restoreFocus(); }
  document.addEventListener("click", event => {
    const link = event.target.closest("a[href]");
    if (!link || event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || (link.target && link.target !== "_self")) return;
    const url = new URL(link.href);
    if (url.origin !== target.origin || url.pathname !== target.pathname) return;
    event.preventDefault();
    if (dialog.open) return;
    opener = link;
    active = true;
    previousPadding = document.body.style.paddingRight;
    const gutter = window.innerWidth - document.documentElement.clientWidth;
    document.body.style.paddingRight = `${parseFloat(getComputedStyle(document.body).paddingRight) + gutter}px`;
    document.documentElement.classList.add("cart-modal-open");
    document.querySelectorAll("[data-header-panel]").forEach(panel => { panel.open = false; });
    window.Notifications.close();
    loading.hidden = true;
    frame.setAttribute("aria-busy", "true");
    dialog.showModal();
    frame.src = target.href;
  });
  frame.addEventListener("load", () => {
    if (!active) return;
    try {
      if (frame.contentDocument?.URL === "about:blank") return;
      loading.hidden = !!frame.contentDocument?.getElementById("cart-app");
    } catch { loading.hidden = false; }
    frame.removeAttribute("aria-busy");
  });
  dialog.querySelector(".cart-drawer-close").addEventListener("click", close);
  dialog.addEventListener("click", event => { if (event.target === dialog) close(); });
  dialog.addEventListener("cancel", event => { event.preventDefault(); close(); });
  dialog.addEventListener("close", () => { if (active) { finishClose(); restoreFocus(); } });
  window.addEventListener("message", event => {
    if (event.origin === window.location.origin && event.source === frame.contentWindow && event.data?.type === "dys-cart-close") close();
  });
})();
