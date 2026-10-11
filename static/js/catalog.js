(function () {
  "use strict";
  const categories = document.querySelector(".category-select");
  if (!categories) return;
  categories.querySelector("button").hidden = true;
  categories.querySelector("select").addEventListener("change", () => categories.requestSubmit());
  const dialog = document.getElementById("product-image-dialog");
  let opener;
  document.querySelectorAll(".product-image-open").forEach(link => {
    link.addEventListener("click", event => {
      if (!dialog.showModal) return;
      event.preventDefault();
      opener = link;
      const source = link.querySelector("img");
      const expanded = dialog.querySelector("img");
      expanded.src = source.src;
      expanded.alt = source.alt;
      dialog.showModal();
    });
  });
  document.getElementById("image-dialog-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener("close", () => opener?.focus({ preventScroll: true }));
})();
