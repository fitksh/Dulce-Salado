(function () {
  "use strict";
  function close() {
    if (window.parent !== window) window.parent.postMessage({ type: "dys-cart-close" }, window.location.origin);
    else window.location.assign("/");
  }
  document.addEventListener("click", event => { if (event.target.closest("[data-close-cart]")) close(); });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !document.querySelector("dialog[open]")) {
      event.preventDefault(); close();
    }
  });
})();
