(function () {
  "use strict";
  const dialog = document.getElementById("order-result-dialog");
  if (!dialog) return;
  let returnFocus;
  // Sólo se acepta el destino preparado por Django; nunca HTML recibido por postMessage.
  function valid(result) {
    if (!result || typeof result.url !== "string" || !/^DYS-\d{6,}$/.test(result.code)) return false;
    try {
      const url = new URL(result.url);
      return url.origin === "https://api.whatsapp.com" && url.pathname === "/send" &&
        !url.username && !url.password && !url.hash && /^\d+$/.test(url.searchParams.get("phone")) &&
        !!url.searchParams.get("text");
    } catch { return false; }
  }
  window.OrderResult = {
    valid,
    show(result, onClose) {
      if (!valid(result) || dialog.open) return false;
      returnFocus = onClose;
      dialog.dataset.code = result.code;
      document.getElementById("whatsapp-ready").href = result.url;
      dialog.showModal();
      document.getElementById("order-result-title").focus({ preventScroll: true });
      return true;
    }
  };
  document.getElementById("order-result-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => {
    document.getElementById("whatsapp-ready").removeAttribute("href");
    const restore = returnFocus; returnFocus = null; restore?.();
  });
})();
