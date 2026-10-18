(function () {
  "use strict";
  const accepted = new WeakMap();
  const selector = "input[data-digits-only]";
  const digits = value => /^[0-9]*$/.test(value);
  function remember(input) {
    if (digits(input.value)) accepted.set(input, input.value);
    else if (!accepted.has(input)) accepted.set(input, "");
  }
  document.addEventListener("focusin", event => {
    if (event.target.matches(selector)) remember(event.target);
  });
  document.addEventListener("beforeinput", event => {
    if (!event.target.matches(selector)) return;
    remember(event.target);
    if (event.data !== null && !digits(event.data)) event.preventDefault();
  });
  document.addEventListener("keydown", event => {
    if (!event.target.matches(selector) || event.ctrlKey || event.metaKey || event.altKey || event.isComposing) return;
    if (event.key.length === 1 && !digits(event.key)) event.preventDefault();
  });
  for (const name of ["paste", "drop"]) document.addEventListener(name, event => {
    if (!event.target.matches(selector)) return;
    const text = (event.clipboardData || event.dataTransfer)?.getData("text");
    if (text !== undefined && !digits(text)) event.preventDefault();
  });
  // Fallback para IME/autocompletado/navegadores sin beforeinput: rechazar la
  // inserción completa. Nunca convertir un pegado como «9,1» en «91».
  document.addEventListener("input", event => {
    const input = event.target;
    if (!input.matches(selector)) return;
    if (!digits(input.value)) {
      input.value = accepted.get(input) || "";
      event.stopImmediatePropagation();
    } else remember(input);
  }, true);
})();
