(function () {
  "use strict";
  const core = window.CartCore;
  const feedback = document.getElementById("cart-feedback");
  const app = document.getElementById("cart-app");
  let items = [], storageFailed = false, serial = 0;
  function announce(message) { feedback.textContent = message; feedback.hidden = false; }
  function count() { document.querySelectorAll("[data-cart-count]").forEach(node => { node.textContent = String(items.length); }); }
  function load() {
    try { items = core.read(window.localStorage); storageFailed = false; }
    catch (error) { storageFailed = true; announce(error instanceof SyntaxError ? "El carrito guardado no se pudo leer. Vaciá el carrito para restablecerlo." : error.message); }
    count();
  }
  function persist() {
    try { core.write(window.localStorage, items); storageFailed = false; }
    catch { storageFailed = true; announce("No se pudo guardar el carrito en este navegador. Habilitá el almacenamiento local para continuar."); }
    count();
  }
  async function refresh() {
    if (!app || storageFailed) { if (app) document.getElementById("cart-loading").hidden = true; return; }
    const requestNumber = ++serial;
    const contents = document.getElementById("cart-contents");
    const loading = document.getElementById("cart-loading");
    const focused = document.activeElement;
    const focusId = contents.contains(focused) ? focused.id : null;
    loading.hidden = false;
    contents.hidden = true;
    contents.setAttribute("aria-busy", "true");
    const data = new FormData();
    data.set("items", JSON.stringify(items));
    data.set("csrfmiddlewaretoken", document.querySelector("#cart-token input").value);
    try {
      const response = await fetch(app.dataset.refreshUrl, { method: "POST", body: data, cache: "no-store", credentials: "same-origin" });
      const html = await response.text();
      if (requestNumber !== serial) return;
      if (!response.ok) throw new Error("No se pudo verificar el carrito. Revisá los datos o volvé a intentarlo.");
      contents.innerHTML = html;
      items = JSON.parse(contents.querySelector("#cart-current-items").textContent);
      persist();
      contents.hidden = false;
      if (focusId) document.getElementById(focusId)?.focus({ preventScroll: true });
    } catch (error) {
      if (requestNumber !== serial) return;
      contents.replaceChildren();
      const notice = document.createElement("p"); notice.className = "notice error"; notice.setAttribute("role", "alert");
      notice.textContent = `${error.message} Los importes no se muestran hasta consultar el catálogo.`;
      const retry = document.createElement("button"); retry.type = "button"; retry.textContent = "Reintentar"; retry.addEventListener("click", refresh);
      contents.append(notice, retry);
    } finally { if (requestNumber === serial) { loading.hidden = true; contents.hidden = false; contents.removeAttribute("aria-busy"); } }
  }
  load();
  document.querySelectorAll(".add-product").forEach(form => {
    form.addEventListener("submit", event => {
      event.preventDefault();
      if (storageFailed) { announce("Revisá el almacenamiento del carrito antes de agregar productos."); return; }
      try {
        const data = new FormData(form);
        items = core.add(items, { id: Number(form.dataset.id), quantity: data.get("quantity"), price_type: data.get("price_type"), revision: form.dataset.revision, sale_unit: form.dataset.unit }, form.elements.quantity.step);
        persist();
        if (!storageFailed) announce("Producto agregado. Podés revisar tu selección en el carrito.");
      } catch (error) { announce(error.message); }
    });
  });
  if (app) {
    document.getElementById("cart-clear").addEventListener("click", () => { items = []; persist(); announce("Carrito vacío."); refresh(); });
    app.addEventListener("click", event => {
      const remove = event.target.closest(".remove-item");
      if (!remove) return;
      items = items.filter(item => item.id !== Number(remove.closest(".cart-item").dataset.id));
      persist(); announce("Producto quitado del carrito."); refresh();
    });
    app.addEventListener("change", event => {
      const row = event.target.closest(".cart-item");
      if (!row || !event.target.matches(".cart-quantity, .cart-price")) return;
      const item = items.find(entry => entry.id === Number(row.dataset.id));
      item.quantity = row.querySelector(".cart-quantity").value;
      item.price_type = row.querySelector(".cart-price").value;
      if (event.target.matches(".cart-quantity")) item.sale_unit = row.dataset.unit;
      persist(); refresh();
    });
    refresh();
  }
  window.addEventListener("storage", event => { if (event.key === core.STORAGE_KEY || event.key === null) { load(); refresh(); } });
  window.addEventListener("pageshow", event => { if (event.persisted) { load(); refresh(); } });
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") { load(); refresh(); } });
})();
