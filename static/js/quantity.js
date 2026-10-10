(function () {
  "use strict";
  function init(container = document) {
    container.querySelectorAll(".quantity-adjust").forEach(button => { button.hidden = false; });
  }
  // El botón conserva el foco del input hasta aplicar el nuevo valor, sin un cambio intermedio.
  document.addEventListener("pointerdown", event => {
    if (event.target.closest(".quantity-adjust")) event.preventDefault();
  });
  document.addEventListener("click", event => {
    const button = event.target.closest(".quantity-adjust");
    if (!button) return;
    const control = button.closest(".quantity-control");
    const input = control.querySelector("input");
    const error = control.querySelector(".quantity-error");
    try {
      input.value = window.CartCore.adjustQuantity(input.value, input.step, Number(button.dataset.direction));
      input.removeAttribute("aria-invalid");
      error.hidden = true;
      input.dispatchEvent(new Event("change", { bubbles: true }));
    } catch (failure) {
      error.textContent = failure.message;
      error.hidden = false;
      input.setAttribute("aria-invalid", "true");
      input.focus({ preventScroll: true });
    }
  });
  document.addEventListener("input", event => {
    const control = event.target.closest(".quantity-control");
    if (control) { control.querySelector(".quantity-error").hidden = true; event.target.removeAttribute("aria-invalid"); }
  });
  window.QuantityControls = { init };
  init();
})();
