(function () {
  "use strict";
  const core = window.CartCore;
  const storageError = document.getElementById("cart-storage-error");
  const reset = document.getElementById("cart-reset");
  const app = document.getElementById("cart-app");
  let items = [], storageFailed = false, serial = 0;
  let reviewing = false, lastQuantityError = null;
  const announce = window.Notifications.show;
  function storageProblem(message) {
    storageError.textContent = message; storageError.classList.add("visually-hidden"); storageError.hidden = false;
    announce(message);
  }
  function cartMessages(contents) {
    const quantityError = contents.querySelector("[data-quantity-error]:not([hidden])");
    if (!quantityError && lastQuantityError) {
      const current = document.querySelector("[data-notification]:not([hidden]) [data-notification-message]");
      if (current?.textContent === lastQuantityError) window.Notifications.close();
    }
    lastQuantityError = quantityError?.textContent || null;
    const error = contents.querySelector("[data-quantity-error]:not([hidden]), [data-cart-error] li, [data-review-error]");
    const notice = contents.querySelector("#cart-notices li, [data-review-notice] li");
    if (error) announce(error.textContent, "error");
    else if (notice) announce(notice.textContent, "warning");
  }
  function setAttribute(node, name, value) {
    if (node.getAttribute(name) !== value) node.setAttribute(name, value);
  }
  function syncBlock(parent, freshParent, selector, before = null) {
    const old = parent.querySelector(selector), fresh = freshParent.querySelector(selector);
    if (!fresh) { old?.remove(); return; }
    if (!old) { parent.insertBefore(fresh, before ? parent.querySelector(before) : null); return; }
    Array.from(old.attributes).forEach(attr => { if (!fresh.hasAttribute(attr.name)) old.removeAttribute(attr.name); });
    Array.from(fresh.attributes).forEach(attr => setAttribute(old, attr.name, attr.value));
    if (old.innerHTML !== fresh.innerHTML) old.replaceChildren(...fresh.childNodes);
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
      const listScroll = oldList.scrollTop;
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
          freshControls.querySelectorAll("input").forEach(control => {
            const old = controls.querySelector(`#${control.id}`);
            const sent = submitted.find(item => String(item.id) === row.dataset.id)?.quantity;
            let unchanged = old.value === sent;
            try { unchanged = core.hundredths(old.value) === core.hundredths(sent); } catch { /* Preservar también borradores inválidos. */ }
            const dirty = previous.dataset.unit === row.dataset.unit && old === focused && old.dataset.dirty === "true" && !unchanged;
            if (!dirty) { if (old.value !== control.value) old.value = control.value; delete old.dataset.dirty; }
            ["pattern", "maxlength", "inputmode"].forEach(name => setAttribute(old, name, control.getAttribute(name)));
            if (old.defaultValue !== control.defaultValue) old.defaultValue = control.defaultValue;
            if (control.hasAttribute("aria-invalid")) setAttribute(old, "aria-invalid", "true");
            else old.removeAttribute("aria-invalid");
            const label = controls.querySelector(`label[for="${control.id}"]`), freshLabel = freshControls.querySelector(`label[for="${control.id}"]`);
            if (label.textContent !== freshLabel.textContent) label.textContent = freshLabel.textContent;
          });
          freshControls.querySelectorAll(".cart-adjust").forEach(button => {
            const old = controls.querySelector(`#${button.id}`);
            setAttribute(old, "aria-label", button.getAttribute("aria-label"));
            if (button.hasAttribute("data-remove")) setAttribute(old, "data-remove", button.dataset.remove);
            [".cart-minus", ".trash-icon"].forEach(selector => {
              const icon = old.querySelector(selector), fresh = button.querySelector(selector);
              if (icon) icon.toggleAttribute("hidden", fresh.hasAttribute("hidden"));
            });
          });
          const error = controls.querySelector(".quantity-error");
          if (!error.hidden) error.hidden = true;
          // Las fotos/títulos y filas intactas no se desmontan en cada cantidad.
          syncBlock(previous, row, ".cart-item-heading", ".product-controls");
          syncBlock(previous, row, ".product-description", ".product-price");
          syncBlock(previous, row, ".product-price", ".product-controls");
          syncBlock(previous, row, ".subtotal", ".product-controls");
          syncBlock(previous, row, "[data-quantity-error]", "[data-cart-error]");
          syncBlock(previous, row, "[data-cart-error]");
          setAttribute(previous, "data-unit", row.dataset.unit);
        } else { previous.replaceWith(row); previous = row; }
        if (oldList.children[index] !== previous) oldList.insertBefore(previous, oldList.children[index] || null);
      });
      const summary = contents.querySelector(".cart-summary"), freshSummary = next.content.querySelector(".cart-summary");
      if (summary.querySelector(".total") && freshSummary.querySelector(".total") && summary.querySelector("#cart-review") && freshSummary.querySelector("#cart-review")) {
        syncBlock(summary, freshSummary, ".total");
        summary.querySelector("#cart-review").disabled = freshSummary.querySelector("#cart-review").disabled;
      } else if (summary.innerHTML !== freshSummary.innerHTML) { summary.replaceChildren(...freshSummary.childNodes); }
      syncBlock(contents, next.content, "#cart-current-items");
      syncBlock(contents, next.content, "#cart-notices");
      oldList.scrollTop = listScroll;
    } else { contents.replaceChildren(next.content); }
    window.QuantityControls.init(contents);
    if (focused?.isConnected && contents.contains(focused)) focused.focus({ preventScroll: true });
    else if (focusId) (contents.querySelector(`#${focusId}`) || contents.querySelector(".empty-state .button, [data-close-cart]"))?.focus({ preventScroll: true });
    window.scrollTo(window.scrollX, scrollTop);
  }
  function syncCartControls() {
    app?.querySelectorAll(".cart-item").forEach(row => {
      const item = items.find(entry => entry.id === Number(row.dataset.id));
      const button = row.querySelector('.cart-adjust[data-direction="-1"]');
      if (!item || !button) return;
      let amount = 0;
      const input = row.querySelector(".cart-quantity");
      const quantity = document.activeElement === input && input.dataset.dirty === "true" ? input.value : item.quantity;
      try { amount = core.hundredths(quantity); } catch { /* La papelera permite quitar una cantidad inválida. */ }
      const remove = amount <= 100 || amount % 100 !== 0 || (item.sale_unit && item.sale_unit !== row.dataset.unit);
      setAttribute(button, "data-remove", String(Boolean(remove)));
      const name = row.querySelector("h2").textContent;
      setAttribute(button, "aria-label", remove ? `Quitar ${name} del carrito` : `Reducir cantidad de ${name}`);
      button.querySelector(".cart-minus").toggleAttribute("hidden", Boolean(remove));
      button.querySelector(".trash-icon").toggleAttribute("hidden", !remove);
    });
  }
  function syncCatalog() {
    document.querySelectorAll(".add-product").forEach(control => {
      const item = items.find(entry => entry.id === Number(control.dataset.id));
      const decrease = control.querySelector(".catalog-decrease");
      const output = control.querySelector(".catalog-amount");
      const increase = control.querySelector(".catalog-increase");
      let one = false;
      const editing = document.activeElement === output && output.dataset.dirty === "true";
      try { one = !!item && core.hundredths(editing ? output.value : item.quantity) === 100; } catch { /* Carrito permite corregirlo. */ }
      decrease.hidden = !item;
      output.hidden = !item;
      const value = item && /^[0-9]{1,7}(\.00)?$/.test(item.quantity) ? item.quantity.replace(/\.00$/, "") : "";
      const dirty = document.activeElement === output && output.dataset.dirty === "true";
      if (!dirty && output.value !== value) output.value = value;
      output.disabled = storageFailed;
      window.QuantityControls.init(control);
      decrease.querySelector(".catalog-trash").toggleAttribute("hidden", !one);
      decrease.querySelector(".catalog-minus").toggleAttribute("hidden", one);
      decrease.setAttribute("aria-label", `${one ? "Eliminar" : "Reducir cantidad de"} ${control.dataset.name}${one ? " del carrito" : ""}`);
      increase.hidden = false;
      increase.disabled = storageFailed;
      decrease.disabled = storageFailed;
    });
  }
  function count() {
    document.querySelectorAll("[data-cart-count]").forEach(node => { if (node.textContent !== String(items.length)) node.textContent = String(items.length); });
    syncCatalog(); syncCartControls();
    if (app) window.QuantityControls.init(app);
  }
  function load() {
    reset.hidden = true;
    try { items = core.read(window.localStorage); storageFailed = false; storageError.hidden = true; }
    catch (error) { items = []; storageFailed = true; reset.hidden = error.name !== "CartDataError"; storageProblem(error.name === "SecurityError" ? "Habilitá el almacenamiento local de este navegador para guardar el carrito." : error.message); }
    count();
  }
  function persist() {
    try { core.write(window.localStorage, items); storageFailed = false; storageError.hidden = true; }
    catch { storageFailed = true; storageProblem("No se pudo guardar el carrito en este navegador. Habilitá el almacenamiento local para continuar."); }
    count();
  }
  async function refresh() {
    if (reviewing) return;
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
    contents.querySelector("#cart-review")?.setAttribute("disabled", "");
    contents.setAttribute("aria-busy", "true");
    const data = new FormData();
    data.set("items", JSON.stringify(items));
    data.set("panel", app.dataset.panel || "0");
    data.set("csrfmiddlewaretoken", document.querySelector("#cart-token input").value);
    try {
      const response = await fetch(app.dataset.refreshUrl, { method: "POST", body: data, cache: "no-store", credentials: "same-origin" });
      const html = await response.text();
      if (requestNumber !== serial) return;
      if (!response.ok) throw new Error("No se pudo verificar el carrito. Revisá los datos o volvé a intentarlo.");
      // Otra pestaña puede escribir antes de que se entregue su evento storage.
      if (JSON.stringify(core.read(window.localStorage)) !== JSON.stringify(submitted)) {
        load(); refresh(); return;
      }
      renderCart(contents, html, submitted, pendingFocus);
      items = JSON.parse(contents.querySelector("#cart-current-items").textContent);
      persist();
      if (storageFailed) contents.querySelector("#cart-review")?.setAttribute("disabled", "");
      else cartMessages(contents);
      contents.classList.remove("is-unverified");
    } catch (error) {
      if (requestNumber !== serial) return;
      contents.classList.add("is-unverified");
      const notice = document.createElement("p"); notice.className = "visually-hidden";
      notice.textContent = `${error.message} Los importes no se muestran hasta consultar el catálogo.`;
      const retry = document.createElement("button"); retry.type = "button"; retry.textContent = "Reintentar"; retry.addEventListener("click", refresh);
      requestError.replaceChildren(notice, retry); requestError.hidden = false;
      announce(notice.textContent);
    } finally { if (requestNumber === serial) { loading.textContent = ""; contents.removeAttribute("aria-busy"); } }
  }
  load();
  reset.addEventListener("click", () => {
    if (reset.hidden) return;
    try {
      window.localStorage.removeItem(core.STORAGE_KEY);
      load(); refresh();
      announce("Carrito restablecido.", "success");
    } catch { storageProblem("No se pudo restablecer el carrito. Revisá el almacenamiento local del navegador."); }
  });
  document.querySelectorAll(".add-product").forEach(control => {
    const input = control.querySelector(".catalog-amount");
    input.addEventListener("input", () => { input.dataset.dirty = "true"; syncCatalog(); });
    input.addEventListener("change", () => {
      const quantity = input.value;
      load();
      if (storageFailed) return;
      try {
        if (!/^[0-9]{1,7}$/.test(quantity) || Number(quantity) < 1) throw new Error("Ingresá una cantidad entera de al menos 1, sin decimales.");
        const next = items.map(item => item.id === Number(control.dataset.id) ? { ...item, quantity: String(Number(quantity)),
          price_type: "retail", sale_unit: control.dataset.unit } : item);
        core.write(window.localStorage, next);
        items = next; delete input.dataset.dirty; input.removeAttribute("aria-invalid"); count();
      } catch (error) { input.setAttribute("aria-invalid", "true"); announce(error.message); }
    });
    control.addEventListener("click", event => {
      const button = event.target.closest(".catalog-increase, .catalog-decrease");
      if (!button) return;
      // Otra pestaña puede haber cambiado el carrito desde el último render.
      load();
      if (storageFailed) return;
      const errorField = control.querySelector(".catalog-error");
      const direction = button.matches(".catalog-increase") ? 1 : -1;
      try {
        const current = items.map(item => item.id === Number(control.dataset.id) && input.dataset.dirty === "true" ? { ...item, quantity: input.value } : item);
        const next = core.changeProduct(current, { id: Number(control.dataset.id), revision: control.dataset.revision,
          sale_unit: control.dataset.unit }, direction);
        // Actualizar la UI sólo después de confirmar la escritura.
        try { core.write(window.localStorage, next); }
        catch { throw new Error("No se pudo guardar el carrito en este navegador. Revisá el almacenamiento local y reintentá."); }
        items = next; delete input.dataset.dirty; count();
        errorField.hidden = true;
        if (button.hidden) control.querySelector(".catalog-increase").focus({ preventScroll: true });
        if (direction > 0) announce(`Se agregó ${control.dataset.name} al carrito.`, "success", {
          label: "Ver carrito", href: document.querySelector(".cart-link").getAttribute("href") });
        else if (!items.some(item => item.id === Number(control.dataset.id))) announce("Producto eliminado", "success");
      } catch (error) {
        errorField.textContent = error.message; errorField.hidden = true;
        announce(error.message);
      }
    });
  });
  if (app) {
    const dialog = document.getElementById("cart-review-dialog");
    const reviewContents = document.getElementById("cart-review-contents");
    let pendingWindow = null, panelClosing = false;
    window.addEventListener("dys-cart-panel-close", () => {
      panelClosing = true; reviewing = false; ++serial;
      closePendingWindow();
      if (dialog.open) dialog.close();
    });
    window.addEventListener("pagehide", () => { ++serial; closePendingWindow(); });
    // Sólo memoria de esta pestaña: los datos personales no van a localStorage.
    const draftHost = window.parent === window ? window : window.parent;
    const draftFields = ["full_name", "delivery_mode", "street", "number", "door", "city"];
    let attempt = null, completedItems = null;
    function rememberDraft() {
      const form = reviewContents.querySelector("#order-customer-form");
      if (!form) return;
      const draft = {};
      draftFields.forEach(name => {
        draft[name] = name === "delivery_mode" ? form.querySelector('[name="delivery_mode"]:checked')?.value : form.elements[name].value;
      });
      draftHost.__dysOrderDraft = draft;
    }
    function addressMode() {
      const form = reviewContents.querySelector("#order-customer-form");
      if (!form) return;
      const delivery = form.querySelector('[name="delivery_mode"]:checked')?.value === "delivery";
      const address = form.querySelector("#delivery-address");
      address.hidden = !delivery; address.disabled = !delivery;
      ["street", "number", "city"].forEach(name => { form.elements[name].required = delivery; });
    }
    function initializeForm() {
      const form = reviewContents.querySelector("#order-customer-form");
      if (!form) return;
      const draft = draftHost.__dysOrderDraft;
      if (draft) draftFields.forEach(name => {
        if (name === "delivery_mode") form.querySelectorAll('[name="delivery_mode"]').forEach(radio => { radio.checked = radio.value === draft[name]; });
        else { form.elements[name].value = draft[name] || ""; form.elements[name].disabled = false; }
      });
      addressMode();
      try {
        window.sessionStorage.setItem("dys-order-confirmation", JSON.stringify({
          items: JSON.stringify(items), token: reviewContents.querySelector("#order-confirmation-token").value
        }));
      } catch { /* El token del formulario sigue disponible durante el reintento. */ }
    }
    function validateCustomer() {
      const form = reviewContents.querySelector("#order-customer-form");
      let first = null;
      ["full_name", "street", "number", "door", "city"].forEach(name => {
        const field = form.elements[name], error = form.querySelector(`#id_${name}_error`);
        const value = field.value.trim().replace(/\s+/g, " ");
        const invalid = !field.disabled && ((field.required && !value) || value.length > field.maxLength);
        error.textContent = invalid ? (!value ? "Completá este campo." : `Usá hasta ${field.maxLength} caracteres.`) : "";
        field.toggleAttribute("aria-invalid", invalid);
        if (invalid && !first) first = field;
      });
      first?.focus(); return !first;
    }
    function closePendingWindow() {
      if (pendingWindow && !pendingWindow.closed) pendingWindow.close();
      pendingWindow = null;
    }
    function prepareWindow() {
      closePendingWindow();
      try {
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
    function clearPreparedItems() {
      try {
        // Conserva productos añadidos/modificados desde otra pestaña durante el envío.
        const current = core.read(window.localStorage);
        items = current.filter(item => !completedItems.some(sent => JSON.stringify(sent) === JSON.stringify(item)));
        core.write(window.localStorage, items);
        storageFailed = false; count();
        reviewContents.querySelector("#cart-clear-error").hidden = true;
        return true;
      } catch {
        reviewContents.querySelector("#cart-clear-error").hidden = false;
        return false;
      }
    }
    function setSubmitting(busy) {
      app.dataset.orderSubmitting = String(busy);
      reviewContents.setAttribute("aria-busy", String(busy));
      reviewContents.querySelectorAll("#review-cancel, #review-continue").forEach(button => { button.disabled = busy; });
    }
    async function review(accepted = false) {
      if (storageFailed || reviewing) return;
      if (accepted && !attempt && !validateCustomer()) return;
      rememberDraft();
      const requestNumber = ++serial;
      reviewing = true;
      let data;
      if (accepted && attempt) data = attempt.data;
      else {
        data = accepted ? new FormData(reviewContents.querySelector("#order-customer-form")) : new FormData();
        data.set("items", JSON.stringify(items));
        data.set("csrfmiddlewaretoken", document.querySelector("#cart-token input").value);
        if (accepted) {
          data.set("accepted", "yes");
          data.set("message_revision", reviewContents.querySelector("#whatsapp-message-revision").value);
          data.set("confirmation_token", reviewContents.querySelector("#order-confirmation-token").value);
          attempt = { data, items: items.map(item => ({ ...item })) };
        } else {
          try {
            const previous = JSON.parse(window.sessionStorage.getItem("dys-order-confirmation"));
            if (previous?.items === JSON.stringify(items)) data.set("confirmation_token", previous.token);
          } catch { /* La revisión genera un token nuevo si no existe. */ }
        }
      }
      if (accepted) { setSubmitting(true); prepareWindow(); }
      try {
        const response = await fetch(accepted ? app.dataset.whatsappUrl : app.dataset.reviewUrl, { method: "POST", body: data, cache: "no-store", credentials: "same-origin" });
        const html = await response.text();
        if (requestNumber !== serial && !accepted) return;
        if (!response.ok) throw new Error("No se pudo completar la preparación. Reintentá con la misma solicitud.");
        reviewContents.innerHTML = html;
        const ready = reviewContents.querySelector("#whatsapp-ready");
        if (ready) {
          completedItems = attempt.items; attempt = null;
          clearPreparedItems();
          draftHost.__dysOrderDraft = null;
          try { window.sessionStorage.removeItem("dys-order-confirmation"); } catch { /* Sin datos personales. */ }
          if (pendingWindow && !pendingWindow.closed) {
            try { pendingWindow.location.replace(ready.href); } catch { closePendingWindow(); }
          }
          pendingWindow = null;
          reviewing = false; setSubmitting(false);
          // La actualización del fondo no cierra el resultado ni vuelve a crear el pedido.
          refresh();
        } else {
          attempt = null; closePendingWindow();
          items = JSON.parse(reviewContents.querySelector("#review-current-items").textContent);
          // Si cambió otra pestaña, no sobrescribir su carrito al volver de una revisión.
          if (JSON.stringify(core.read(window.localStorage)) === data.get("items")) persist();
          initializeForm(); cartMessages(reviewContents);
          if (reviewContents.querySelector("[data-review-required]")) {
            try { window.sessionStorage.removeItem("dys-order-confirmation"); } catch { /* Revisión nueva requerida. */ }
          }
        }
        if (!dialog.open) dialog.showModal();
        document.getElementById("review-title").focus({ preventScroll: true });
        dialog.scrollTop = 0;
      } catch (error) {
        closePendingWindow();
        // Puede haberse guardado aunque se pierda la respuesta: repetir exactamente la misma confirmación.
        if (accepted && attempt) {
          reviewContents.querySelectorAll("#order-customer-form input").forEach(field => { field.disabled = true; });
          announce("No pudimos obtener la respuesta. Conservamos el carrito y tus datos. Presioná Enviar para recuperar el mismo pedido sin duplicarlo.", "error");
        } else announce(error instanceof TypeError ? "No se pudo verificar el carrito. Revisá la conexión y reintentá." : error.message);
      } finally {
        reviewing = false;
        app.dataset.orderSubmitting = "false";
        reviewContents.setAttribute("aria-busy", "false");
        // No rehabilitar el envío si la respuesta exige una nueva revisión.
        if (attempt) setSubmitting(false);
      }
    }
    dialog.addEventListener("cancel", event => {
      if (app.dataset.orderSubmitting === "true") event.preventDefault();
    });
    dialog.addEventListener("close", () => {
      rememberDraft(); closePendingWindow();
      window.Notifications.close(false, dialog);
      reviewing = false; ++serial;
      if (panelClosing) return;
      document.getElementById("cart-review")?.focus({ preventScroll: true });
      refresh();
    });
    dialog.addEventListener("input", rememberDraft);
    dialog.addEventListener("change", () => { rememberDraft(); addressMode(); });
    dialog.addEventListener("submit", event => {
      if (event.target.id === "order-customer-form") { event.preventDefault(); review(true); }
    });
    dialog.addEventListener("click", event => {
      if (event.target.closest("#review-cancel") && app.dataset.orderSubmitting !== "true") dialog.close();
      if (event.target.closest("#retry-cart-clear")) { clearPreparedItems(); refresh(); }
    });
    app.addEventListener("click", event => {
      if (event.target.closest("#cart-review")) {
        if (attempt) { dialog.showModal(); document.getElementById("review-title").focus(); }
        else review();
        return;
      }
      const button = event.target.closest(".cart-adjust, .remove-item");
      if (!button) return;
      event.stopPropagation();
      load();
      if (storageFailed) return;
      const row = button.closest(".cart-item");
      const id = Number(row.dataset.id);
      if (!items.some(item => item.id === id)) { refresh(); return; }
      const remove = button.matches(".remove-item") || button.dataset.remove === "true";
      try {
        const input = row.querySelector(".cart-quantity");
        const current = items.map(item => item.id === id && input === document.activeElement && input.dataset.dirty === "true" ? { ...item, quantity: input.value } : item);
        const next = remove ? current.filter(item => item.id !== id) : core.changeProduct(current,
          { id, sale_unit: row.dataset.unit }, Number(button.dataset.direction));
        try { core.write(window.localStorage, next); }
        catch { throw new Error("No se pudo guardar el carrito en este navegador. Revisá el almacenamiento local y reintentá."); }
        items = next;
        if (input && !remove) {
          input.value = items.find(item => item.id === id).quantity.replace(/\.00$/, "");
          delete input.dataset.dirty;
        }
        count();
        if (remove) {
          const remaining = Array.from(app.querySelectorAll(".cart-item")).find(other => other !== row);
          (remaining?.querySelector(".cart-adjust, .remove-item") || document.getElementById("cart-review"))?.focus({ preventScroll: true });
        }
        refresh();
      } catch (error) {
        row.querySelector(".cart-quantity")?.setAttribute("aria-invalid", "true");
        announce(error.message);
      }
    });
    app.addEventListener("input", event => {
      if (event.target.matches(".cart-quantity")) { event.target.dataset.dirty = "true"; syncCartControls(); }
    });
    app.addEventListener("change", event => {
      const row = event.target.closest(".cart-item");
      if (!row || !event.target.matches(".cart-quantity")) return;
      const item = items.find(entry => entry.id === Number(row.dataset.id));
      if (!item) return;
      item.quantity = row.querySelector(".cart-quantity").value;
      delete event.target.dataset.dirty;
      item.price_type = "retail";
      if (event.target.matches(".cart-quantity")) item.sale_unit = row.dataset.unit;
      persist(); refresh();
    });
    refresh();
  }
  window.addEventListener("storage", event => {
    if (event.key !== core.STORAGE_KEY && event.key !== null) return;
    if (app?.dataset.orderSubmitting === "true") return;
    const dialog = document.getElementById("cart-review-dialog");
    if (dialog?.open && !document.getElementById("order-result")) {
      dialog.close(); announce("El carrito cambió en otra pestaña. Revisalo nuevamente.", "warning");
    }
    load(); refresh();
  });
  window.addEventListener("pageshow", event => { if (event.persisted) { load(); refresh(); } });
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible" && !reviewing) { load(); refresh(); } });
})();
