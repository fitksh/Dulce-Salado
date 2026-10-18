(function () {
  "use strict";
  function resize(input) {
    const width = `${Math.max(3, Math.min(9, input.value.length + 1))}ch`;
    if (input.style.width !== width) input.style.width = width;
  }
  function init(container = document) {
    container.querySelectorAll(".quantity-adjust").forEach(button => { button.hidden = false; });
    container.querySelectorAll(".cart-quantity, .catalog-amount").forEach(resize);
  }
  document.addEventListener("invalid", event => {
    if (!event.target.matches(".cart-quantity, .catalog-amount")) return;
    event.preventDefault();
    event.target.setAttribute("aria-invalid", "true");
    window.Notifications.show("Ingresá una cantidad entera de al menos 1, sin decimales.");
  }, true);
  document.addEventListener("pointerdown", event => {
    if (event.target.closest(".quantity-adjust, .catalog-increase, .catalog-decrease")) event.preventDefault();
  });
  document.addEventListener("input", event => {
    if (event.target.matches(".cart-quantity, .catalog-amount")) {
      resize(event.target); event.target.removeAttribute("aria-invalid");
    }
  });
  window.QuantityControls = { init };
  init();
})();
