(function () {
  "use strict";
  const hosts = Array.from(document.querySelectorAll("[data-notification]"));
  let active, opener, timer, remaining, started;
  function close(restoreFocus = false, container = null) {
    if (container && active && !container.contains(active)) return;
    clearTimeout(timer);
    timer = null;
    if (!active) return;
    if (restoreFocus && active.contains(document.activeElement) && opener?.isConnected) opener.focus({ preventScroll: true });
    active.hidden = true;
    active = null;
  }
  function pause() {
    if (!timer) return;
    clearTimeout(timer); timer = null;
    remaining = Math.max(0, remaining - (performance.now() - started));
  }
  function resume() {
    if (!active || timer || active.matches(":hover") || active.contains(document.activeElement)) return;
    started = performance.now();
    timer = setTimeout(() => close(), remaining);
  }
  function show(message, kind = "error", action = null) {
    close();
    // Dentro del diálogo modal, el aviso debe seguir siendo operable (el resto es inert).
    active = document.querySelector("dialog[open] [data-notification]") || hosts[0];
    opener = document.activeElement;
    active.className = `floating-notice notice ${kind}`;
    const text = active.querySelector("[data-notification-message]");
    text.setAttribute("role", kind === "error" ? "alert" : "status");
    text.setAttribute("aria-live", kind === "error" ? "assertive" : "polite");
    const link = active.querySelector("[data-notification-action]");
    link.hidden = !action;
    if (action) { link.textContent = action.label; link.href = action.href; }
    active.hidden = false;
    text.textContent = message;
    remaining = ["error", "warning"].includes(kind) ? 8000 : 5000;
    resume();
  }
  hosts.forEach(host => {
    host.querySelector("[data-notification-close]").addEventListener("click", () => close(true));
    host.addEventListener("mouseenter", pause);
    host.addEventListener("mouseleave", resume);
    host.addEventListener("focusin", pause);
    host.addEventListener("focusout", () => setTimeout(resume, 0));
  });
  window.Notifications = { show, close };
})();
