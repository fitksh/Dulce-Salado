(function () {
  "use strict";
  const categories = document.querySelector(".category-select");
  if (categories) {
    categories.querySelector("button").hidden = true;
    categories.querySelector("select").addEventListener("change", () => categories.requestSubmit());
  }
  const dialog = document.getElementById("product-image-dialog");
  let opener;
  if (!dialog) return;
  document.addEventListener("click", event => {
    const link = event.target.closest(".product-image-open");
    if (!link || !dialog.showModal) return;
    event.preventDefault();
    opener = link;
    const source = link.querySelector("img");
    const expanded = dialog.querySelector("img");
    expanded.src = source.src;
    expanded.alt = source.alt;
    dialog.showModal();
  });
  document.getElementById("image-dialog-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener("close", () => {
    // El navegador ya restaura el foco; no volver a quitarlo si el usuario siguió con otro control.
    if (document.activeElement !== document.body && !dialog.contains(document.activeElement)) return;
    const target = opener?.isConnected ? opener : Array.from(document.querySelectorAll(".product-image-open")).find(link => link.href === opener?.href);
    target?.focus({ preventScroll: true });
  });
})();
