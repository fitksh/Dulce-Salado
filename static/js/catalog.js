(function () {
  "use strict";
  const categories = document.querySelector(".category-select");
  if (!categories) return;
  categories.querySelector("button").hidden = true;
  categories.querySelector("select").addEventListener("change", () => categories.requestSubmit());
})();
