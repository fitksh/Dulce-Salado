(function () {
  "use strict";
  const core = window.CartCore;
  const feedback = document.getElementById("cart-feedback");
  const app = document.getElementById("cart-app");
  let items = [], storageFailed = false, serial = 0;
  let reviewing = false;
  let feedbackTimer;
  function announce(message, kind = "error") {
    clearTimeout(feedbackTimer);
    feedback.className = `feedback ${kind}`;
    feedback.setAttribute("role", kind === "error" ? "alert" : "status");
    feedback.textContent = message; feedback.hidden = false;
    if (kind === "success") feedbackTimer = setTimeout(() => { feedback.hidden = true; }, 8000);
  }
  function renderCart(contents, html, submitted) {
    const focused = document.activeElement;
    const scrollTop = window.scrollY;
    const next = document.createElement("template");
    next.innerHTML = html;
    // Reutilizar controles del mismo producto/unidad evita perder edición y foco.
    next.content.querySelectorAll(".cart-item").forEach(row => {
      const previous = contents.querySelector(`.cart-item[data-id="${row.dataset.id}"]`);
      if (!previous || previous.dataset.unit !== row.dataset.unit) return;
      row.querySelectorAll("input, select, button").forEach(control => {
        const selector = control.id ? `#${control.id}` : control.dataset.direction ? `[data-direction="${control.dataset.direction}"]` : ".remove-item";
        const old = previous.querySelector(selector);
        if (!old) return;
        if (control.tagName === "INPUT") {
          const dirty = old === focused && old.value !== submitted.find(item => String(item.id) === row.dataset.id)?.quantity;
          if (!dirty) old.value = control.value;
          old.min = control.min; old.step = control.step;
          old.removeAttribute("aria-invalid");
        } else if (control.tagName === "SELECT") {
          old.innerHTML = control.innerHTML; old.value = control.value;
        }
        control.replaceWith(old);
      });
    });
    contents.replaceChildren(next.content);
    window.QuantityControls.init(contents);
    if (focused?.isConnected && contents.contains(focused)) focused.focus({ preventScroll: true });
    window.scrollTo(window.scrollX, scrollTop);
  }
  function count() { document.querySelectorAll("[data-cart-count]").forEach(node => { node.textContent = String(items.length); }); }
  function load() {
    try { items = core.read(window.localStorage); storageFailed = false; }
    catch (error) { items = []; storageFailed = true; announce(error instanceof SyntaxError ? "El carrito guardado no se pudo leer. Vaciá el carrito para restablecerlo." : error.name === "SecurityError" ? "Habilitá el almacenamiento local de este navegador para guardar el carrito." : error.message); }
    count();
  }
  function persist() {
    try { core.write(window.localStorage, items); storageFailed = false; }
    catch { storageFailed = true; announce("No se pudo guardar el carrito en este navegador. Habilitá el almacenamiento local para continuar."); }
    count();
  }
  async function refresh() {
    if (app) { const dialog = document.getElementById("cart-review-dialog"); if (dialog.open) dialog.close(); }
    if (!app) return;
    if (storageFailed) { ++serial; document.getElementById("cart-loading").textContent = ""; document.getElementById("cart-contents").replaceChildren(); return; }
    const requestNumber = ++serial;
    const contents = document.getElementById("cart-contents");
    const loading = document.getElementById("cart-loading");
    const requestError = document.getElementById("cart-request-error");
    const submitted = items.map(item => ({ ...item }));
    loading.textContent = "Consultando el catálogo vigente…";
    requestError.hidden = true;
    contents.classList.add("is-unverified");
    contents.querySelector("#cart-review")?.setAttribute("disabled", "");
    contents.setAttribute("aria-busy", "true");
    const data = new FormData();
    data.set("items", JSON.stringify(items));
    data.set("csrfmiddlewaretoken", document.querySelector("#cart-token input").value);
    try {
      const response = await fetch(app.dataset.refreshUrl, { method: "POST", body: data, cache: "no-store", credentials: "same-origin" });
      const html = await response.text();
      if (requestNumber !== serial) return;
      if (!response.ok) throw new Error("No se pudo verificar el carrito. Revisá los datos o volvé a intentarlo.");
      renderCart(contents, html, submitted);
      items = JSON.parse(contents.querySelector("#cart-current-items").textContent);
      persist();
      if (storageFailed) contents.querySelector("#cart-review")?.setAttribute("disabled", "");
      contents.classList.remove("is-unverified");
    } catch (error) {
      if (requestNumber !== serial) return;
      const notice = document.createElement("p"); notice.className = "notice error"; notice.setAttribute("role", "alert");
      notice.textContent = `${error.message} Los importes no se muestran hasta consultar el catálogo.`;
      const retry = document.createElement("button"); retry.type = "button"; retry.textContent = "Reintentar"; retry.addEventListener("click", refresh);
      requestError.replaceChildren(notice, retry); requestError.hidden = false;
    } finally { if (requestNumber === serial) { loading.textContent = ""; contents.removeAttribute("aria-busy"); } }
  }
  load();
  document.querySelectorAll(".add-product").forEach(form => {
    let successTimer;
    form.addEventListener("submit", event => {
      event.preventDefault();
      if (storageFailed) { announce("Revisá el almacenamiento del carrito antes de agregar productos."); return; }
      try {
        const data = new FormData(form);
        items = core.add(items, { id: Number(form.dataset.id), quantity: data.get("quantity"), price_type: data.get("price_type"), revision: form.dataset.revision, sale_unit: form.dataset.unit }, form.elements.quantity.step);
        persist();
        if (!storageFailed) {
          feedback.hidden = true;
          const confirmation = form.querySelector(".product-feedback");
          confirmation.hidden = false;
          clearTimeout(successTimer);
          successTimer = setTimeout(() => { confirmation.hidden = true; }, 8000);
        }
      } catch (error) { announce(error.message); }
    });
  });
  if (app) {
    const dialog = document.getElementById("cart-review-dialog");
    const reviewContents = document.getElementById("cart-review-contents");
    async function review(accepted = false) {
      if (storageFailed || reviewing) return;
      const requestNumber = ++serial;
      reviewing = true;
      const data = new FormData();
      data.set("items", JSON.stringify(items));
      data.set("csrfmiddlewaretoken", document.querySelector("#cart-token input").value);
      if (accepted) data.set("accepted", "yes");
      if (accepted) document.getElementById("review-continue").disabled = true;
      try {
        const response = await fetch(accepted ? app.dataset.whatsappUrl : app.dataset.reviewUrl, { method: "POST", body: data, cache: "no-store", credentials: "same-origin" });
        const html = await response.text();
        if (requestNumber !== serial) return;
        if (!response.ok) throw new Error("No se pudo verificar el mensaje. Volvé al carrito y reintentá.");
        reviewContents.innerHTML = html;
        items = JSON.parse(reviewContents.querySelector("#review-current-items").textContent);
        persist();
        const ready = reviewContents.querySelector("#whatsapp-ready");
        if (ready && !storageFailed) { window.location.assign(ready.href); return; }
        if (!dialog.open) dialog.showModal();
        if (storageFailed) document.getElementById("review-continue").disabled = true;
        document.getElementById("review-title").focus({ preventScroll: true });
        dialog.scrollTop = 0;
      } catch (error) { if (requestNumber === serial) { if (dialog.open) dialog.close(); announce(error.message); } }
      finally { if (requestNumber === serial) reviewing = false; }
    }
    dialog.addEventListener("close", () => { reviewing = false; ++serial; refresh(); });
    dialog.addEventListener("click", async event => {
      if (event.target.closest("#review-cancel")) dialog.close();
      if (event.target.closest("#review-continue")) review(true);
      if (event.target.closest("#copy-message")) {
        const field = document.getElementById("whatsapp-message");
        try { await navigator.clipboard.writeText(field.value); event.target.textContent = "Mensaje copiado"; }
        catch { field.focus(); field.select(); event.target.textContent = "Seleccionado: copiá el texto"; }
      }
    });
    document.getElementById("cart-clear").addEventListener("click", () => { items = []; persist(); if (!storageFailed) announce("Carrito vacío.", "success"); refresh(); });
    app.addEventListener("click", event => {
      if (event.target.closest("#cart-review")) { review(); return; }
      const remove = event.target.closest(".remove-item");
      if (!remove) return;
      items = items.filter(item => item.id !== Number(remove.closest(".cart-item").dataset.id));
      persist(); if (!storageFailed) announce("Producto quitado del carrito.", "success"); refresh();
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
