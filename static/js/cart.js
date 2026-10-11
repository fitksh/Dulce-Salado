(function () {
  "use strict";
  const core = window.CartCore;
  const storageError = document.getElementById("cart-storage-error");
  const app = document.getElementById("cart-app");
  let items = [], storageFailed = false, serial = 0;
  let reviewing = false;
  const announce = window.Notifications.show;
  function storageProblem(message) {
    storageError.textContent = message; storageError.hidden = false;
    announce(message);
  }
  function cartMessages(contents) {
    const error = contents.querySelector("[data-cart-error] li, [data-review-error]");
    const notice = contents.querySelector("#cart-notices li, [data-review-notice] li");
    if (error) announce(error.textContent, "error");
    else if (notice) announce(notice.textContent, "warning");
  }
  function renderCart(contents, html, submitted, pendingFocus) {
    const focused = document.activeElement;
    const focusId = focused?.id || (focused === document.body ? pendingFocus : null);
    const scrollTop = window.scrollY;
    const next = document.createElement("template");
    next.innerHTML = html;
    const oldList = contents.querySelector(".cart-items");
    const newList = next.content.querySelector(".cart-items");
    if (oldList && newList) {
      const rows = Array.from(newList.children);
      const ids = new Set(rows.map(row => row.dataset.id));
      Array.from(oldList.children).forEach(row => { if (!ids.has(row.dataset.id)) row.remove(); });
      rows.forEach((row, index) => {
        let previous = oldList.querySelector(`.cart-item[data-id="${row.dataset.id}"]`);
        if (!previous) { oldList.insertBefore(row, oldList.children[index] || null); return; }
        const controls = previous.querySelector(".product-controls");
        const freshControls = row.querySelector(".product-controls");
        if (controls && freshControls) {
          // El contenedor sigue conectado: desmontar un input enfocado dispara blur/change nativo.
          freshControls.querySelectorAll("input, select").forEach(control => {
            const old = controls.querySelector(`#${control.id}`);
            if (control.tagName === "INPUT") {
              const dirty = previous.dataset.unit === row.dataset.unit && old === focused && old.value !== submitted.find(item => String(item.id) === row.dataset.id)?.quantity;
              if (!dirty) old.value = control.value;
              old.min = control.min; old.step = control.step; old.inputMode = control.inputMode;
              old.removeAttribute("aria-invalid");
            } else { old.innerHTML = control.innerHTML; old.value = control.value; }
            controls.querySelector(`label[for="${control.id}"]`).textContent = freshControls.querySelector(`label[for="${control.id}"]`).textContent;
          });
          controls.querySelector(".quantity-error").hidden = true;
          Array.from(previous.childNodes).forEach(node => { if (node !== controls) node.remove(); });
          let after = false;
          Array.from(row.childNodes).forEach(node => {
            if (node === freshControls) { after = true; return; }
            if (after) previous.append(node); else previous.insertBefore(node, controls);
          });
          previous.dataset.unit = row.dataset.unit;
        } else { previous.replaceWith(row); previous = row; }
        if (oldList.children[index] !== previous) oldList.insertBefore(previous, oldList.children[index] || null);
      });
      contents.querySelector(".cart-summary").innerHTML = next.content.querySelector(".cart-summary").innerHTML;
      contents.querySelector("#cart-current-items").textContent = next.content.querySelector("#cart-current-items").textContent;
      contents.querySelector("#cart-notices").replaceChildren(...next.content.querySelector("#cart-notices").childNodes);
    } else { contents.replaceChildren(next.content); }
    window.QuantityControls.init(contents);
    if (focused?.isConnected && contents.contains(focused)) focused.focus({ preventScroll: true });
    else if (focusId) contents.querySelector(`#${focusId}`)?.focus({ preventScroll: true });
    window.scrollTo(window.scrollX, scrollTop);
  }
  function count() { document.querySelectorAll("[data-cart-count]").forEach(node => { node.textContent = String(items.length); }); }
  function load() {
    try { items = core.read(window.localStorage); storageFailed = false; storageError.hidden = true; }
    catch (error) { items = []; storageFailed = true; storageProblem(error instanceof SyntaxError ? "El carrito guardado no se pudo leer. Vaciá el carrito para restablecerlo." : error.name === "SecurityError" ? "Habilitá el almacenamiento local de este navegador para guardar el carrito." : error.message); }
    count();
  }
  function persist() {
    try { core.write(window.localStorage, items); storageFailed = false; storageError.hidden = true; }
    catch { storageFailed = true; storageProblem("No se pudo guardar el carrito en este navegador. Habilitá el almacenamiento local para continuar."); }
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
    const pendingFocus = contents.contains(document.activeElement) ? document.activeElement.id : null;
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
      renderCart(contents, html, submitted, pendingFocus);
      items = JSON.parse(contents.querySelector("#cart-current-items").textContent);
      persist();
      if (storageFailed) contents.querySelector("#cart-review")?.setAttribute("disabled", "");
      else cartMessages(contents);
      contents.classList.remove("is-unverified");
    } catch (error) {
      if (requestNumber !== serial) return;
      const notice = document.createElement("p"); notice.className = "notice error";
      notice.textContent = `${error.message} Los importes no se muestran hasta consultar el catálogo.`;
      const retry = document.createElement("button"); retry.type = "button"; retry.textContent = "Reintentar"; retry.addEventListener("click", refresh);
      requestError.replaceChildren(notice, retry); requestError.hidden = false;
      announce(notice.textContent);
    } finally { if (requestNumber === serial) { loading.textContent = ""; contents.removeAttribute("aria-busy"); } }
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
        if (!storageFailed) {
          announce("Producto agregado al carrito.", "success", { label: "Ver carrito", href: document.querySelector(".cart-link").getAttribute("href") });
        }
      } catch (error) { announce(error.message); }
    });
  });
  if (app) {
    const dialog = document.getElementById("cart-review-dialog");
    const reviewContents = document.getElementById("cart-review-contents");
    let pendingWindow = null;
    function closePendingWindow() {
      if (pendingWindow && !pendingWindow.closed) pendingWindow.close();
      pendingWindow = null;
    }
    function prepareWindow() {
      closePendingWindow();
      try {
        // Se inicia en el clic, antes del await. Conservamos el handle para cancelar.
        pendingWindow = window.open("about:blank", "_blank");
        if (!pendingWindow) return;
        pendingWindow.opener = null;
        const meta = pendingWindow.document.createElement("meta");
        meta.name = "referrer"; meta.content = "no-referrer";
        pendingWindow.document.head.append(meta);
        pendingWindow.document.documentElement.lang = "es-AR";
        pendingWindow.document.title = "Preparando WhatsApp · Dulce y Salado";
        pendingWindow.document.body.textContent = "Verificando precios y cantidades antes de abrir WhatsApp…";
      } catch { closePendingWindow(); }
    }
    async function review(accepted = false) {
      if (storageFailed || reviewing) return;
      const requestNumber = ++serial;
      reviewing = true;
      const data = new FormData();
      data.set("items", JSON.stringify(items));
      data.set("csrfmiddlewaretoken", document.querySelector("#cart-token input").value);
      if (accepted) data.set("accepted", "yes");
      if (accepted) { document.getElementById("review-continue").disabled = true; prepareWindow(); }
      try {
        const response = await fetch(accepted ? app.dataset.whatsappUrl : app.dataset.reviewUrl, { method: "POST", body: data, cache: "no-store", credentials: "same-origin" });
        const html = await response.text();
        if (requestNumber !== serial) return;
        if (accepted && !dialog.open) { closePendingWindow(); return; }
        if (!response.ok) throw new Error("No se pudo verificar el mensaje. Volvé al carrito y reintentá.");
        reviewContents.innerHTML = html;
        items = JSON.parse(reviewContents.querySelector("#review-current-items").textContent);
        persist();
        const ready = reviewContents.querySelector("#whatsapp-ready");
        if (ready && !storageFailed) {
          let opened = false;
          if (pendingWindow && !pendingWindow.closed) {
            try { pendingWindow.location.replace(ready.href); opened = true; }
            catch { closePendingWindow(); }
          }
          pendingWindow = null;
          document.getElementById("review-continue").hidden = true;
          announce(opened ? "Mensaje preparado. Conservás el carrito en esta pestaña." : "Mensaje preparado. Usá el enlace para abrir WhatsApp en otra pestaña.", "info");
          return;
        }
        closePendingWindow();
        if (ready) ready.remove();
        if (!dialog.open) dialog.showModal();
        if (storageFailed) document.getElementById("review-continue").disabled = true;
        else cartMessages(reviewContents);
        document.getElementById("review-title").focus({ preventScroll: true });
        dialog.scrollTop = 0;
      } catch (error) { if (requestNumber === serial) { closePendingWindow(); if (dialog.open) dialog.close(); announce(error instanceof TypeError ? "No se pudo verificar el mensaje. Revisá la conexión y reintentá desde el carrito." : error.message); } }
      finally { if (requestNumber === serial) reviewing = false; }
    }
    dialog.addEventListener("close", () => {
      closePendingWindow();
      window.Notifications.close(false, dialog);
      reviewing = false; ++serial;
      document.getElementById("cart-review")?.focus({ preventScroll: true });
      refresh();
    });
    dialog.addEventListener("click", async event => {
      if (event.target.closest("#review-cancel")) dialog.close();
      if (event.target.closest("#review-continue")) review(true);
      if (event.target.closest("#copy-message")) {
        const field = document.getElementById("whatsapp-message");
        try { await navigator.clipboard.writeText(field.value); announce("Mensaje copiado.", "success"); }
        catch { field.focus(); field.select(); announce("Copiá el texto seleccionado para pegarlo en WhatsApp.", "info"); }
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
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible" && !reviewing) { load(); refresh(); } });
})();
