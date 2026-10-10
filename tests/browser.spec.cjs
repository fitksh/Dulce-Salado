// Sólo pruebas: herramientas instaladas en .qa, sin dependencias del sitio.
const test = require("node:test");
const assert = require("node:assert/strict");
const { mkdirSync, readFileSync } = require("node:fs");
const { chromium } = require("../.qa/node_modules/playwright");
const { default: AxeBuilder } = require("../.qa/node_modules/@axe-core/playwright");
const base = process.env.QA_BASE_URL || "http://127.0.0.1:8001";

test("MVP en navegador aislado: catálogo, carrito, Admin y WhatsApp", { timeout: 120000 }, async t => {
  const browser = await chromium.launch();
  t.after(() => browser.close());
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  for (let attempt = 0; attempt < 30; attempt++) {
    const response = await context.request.get(base, { timeout: 1000 }).catch(() => null);
    if (response?.ok()) break;
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  let page = await context.newPage();
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(base);
  await page.locator(".product-card").first().waitFor();
  const chocolateId = await page.locator(".add-product").first().getAttribute("data-id");
  mkdirSync(".qa/screenshots", { recursive: true });
  async function accessible(target = page) {
    const result = await new AxeBuilder({ page: target }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    assert.deepEqual(result.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) })), []);
  }
  async function waitCart(text) { await page.locator(".total").filter({ hasText: text }).waitFor(); }
  async function setQuantity(value) {
    const input = page.locator(".cart-quantity").first();
    await input.fill(value);
    await input.press("Tab");
  }
  const admin = await context.newPage();
  await admin.goto(`${base}/admin/login/`);
  await admin.locator("#id_username").fill("qa-admin");
  await admin.locator("#id_password").fill("qa-only-password-582");
  await admin.locator('input[type="submit"]').click();
  async function editPrices(retail, wholesale) {
    await admin.goto(`${base}/admin/catalog/product/${chocolateId}/change/`);
    await admin.locator("#id_retail_price").fill(retail);
    await admin.locator("#id_wholesale_price").fill(wholesale);
    await admin.locator('input[name="_save"]').click();
    await admin.locator(".messagelist .success").waitFor();
    assert.equal(await admin.locator(".messagelist .success").count(), 1);
    assert.equal(await admin.locator(".messagelist .success").isVisible(), true);
  }

  await t.test("responsive, sólo activos, búsqueda y WCAG automatizado", async () => {
    assert.equal(await page.locator(".product-card").count(), 12);
    assert.equal(await page.getByText("QA Invisible").count(), 0);
    for (const width of [360, 390, 430, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const header = await page.locator(".header-inner").evaluate(node => {
        const brand = node.querySelector(".brand").getBoundingClientRect();
        const cart = node.querySelector(".cart-link").getBoundingClientRect();
        return { sameRow: Math.abs((brand.top + brand.bottom) / 2 - (cart.top + cart.bottom) / 2) < 2, contained: cart.right <= node.getBoundingClientRect().right + 1 };
      });
      assert.equal(header.sameRow && header.contained, true);
      const targets = await page.locator("button, input:not([type=hidden]), select, .button, .chip").evaluateAll(nodes => nodes.filter(n => n.getBoundingClientRect().height > 0).map(n => ({ tag: n.tagName, height: n.getBoundingClientRect().height })));
      assert.equal(targets.every(target => target.height >= 44), true, JSON.stringify(targets));
      const steppers = await page.locator(".quantity-adjust").evaluateAll(nodes => nodes.map(n => n.getBoundingClientRect().width));
      assert.equal(steppers.every(width => width >= 44), true);
      await page.screenshot({ path: `.qa/screenshots/catalog-${width}.png`, fullPage: true });
    }
    await accessible();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator("#catalog-search").fill("QA Marca");
    await page.getByRole("button", { name: "Buscar", exact: true }).click();
    assert.equal(await page.locator(".product-card").count(), 1);
    await page.locator("#category-filter").selectOption("qa-cotillon");
    await page.getByRole("button", { name: "Filtrar", exact: true }).click();
    await page.getByRole("heading", { name: "No encontramos productos" }).waitFor();
    assert.equal(await page.locator("#catalog-search").inputValue(), "QA Marca");
    await page.goto(base);
  });

  await t.test("categorías funcionan sin JavaScript y botones respetan decimales/mínimo", async () => {
    const plain = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 360, height: 844 } });
    const plainPage = await plain.newPage();
    await plainPage.goto(`${base}/?q=QA`);
    await plainPage.locator("#category-filter").selectOption("qa-cotillon");
    await plainPage.getByRole("button", { name: "Filtrar", exact: true }).click();
    assert.equal(await plainPage.locator(".product-card").count(), 1);
    assert.equal(await plainPage.locator("#catalog-search").inputValue(), "QA");
    assert.equal(await plainPage.locator("#category-filter").inputValue(), "qa-cotillon");
    await plain.close();
    const card = page.locator(".product-card").first();
    await card.getByRole("button", { name: /Reducir cantidad/ }).click();
    assert.equal(await card.locator('input[name="quantity"]').inputValue(), "0.10");
    await card.getByRole("button", { name: /Aumentar cantidad/ }).click();
    await card.getByRole("button", { name: /Aumentar cantidad/ }).click();
    assert.equal(await card.locator('input[name="quantity"]').inputValue(), "0.30");
    await card.locator('input[name="quantity"]').fill("0.15");
    await card.getByRole("button", { name: /Aumentar cantidad/ }).click();
    await card.getByRole("alert").filter({ hasText: /múltiplo/ }).waitFor();
    await card.locator('input[name="quantity"]').fill("0.10");
  });

  await t.test("cantidad, mayorista manual y persistencia al cerrar pestaña", async () => {
    const card = page.locator(".product-card").filter({ hasText: "QA Chocolate (test)" });
    await card.locator('input[name="quantity"]').fill("0.3");
    await card.locator('select[name="price_type"]').selectOption("wholesale");
    await card.getByRole("button", { name: "Agregar al carrito" }).click();
    await page.getByRole("status").filter({ hasText: "Producto agregado" }).waitFor();
    assert.equal(await card.getByRole("link", { name: "Ver carrito" }).isVisible(), true);
    assert.equal(await page.locator("[data-cart-count]").innerText(), "1");
    await accessible();
    const stored = JSON.parse(await page.evaluate(() => localStorage.getItem("dulce-salado.cart.v1")));
    assert.equal(stored.items[0].quantity, "0.30");
    assert.equal(stored.items[0].price_type, "wholesale");
    assert.equal("price" in stored.items[0], false);
    await page.close();
    page = await context.newPage();
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(`${base}/carrito/`);
    await waitCart("$ 27,15");
    await accessible();
    await page.getByRole("button", { name: /Aumentar cantidad/ }).click();
    await waitCart("$ 36,20");
    await page.getByRole("button", { name: /Reducir cantidad/ }).click();
    await waitCart("$ 27,15");
    await page.screenshot({ path: ".qa/screenshots/cart-mobile.png", fullPage: true });
    await setQuantity("0.5");
    await waitCart("$ 45,25");
    await setQuantity("0.15");
    await page.getByText(/La cantidad debe ser positiva/).waitFor();
    assert.equal(await page.locator("#cart-review").isDisabled(), true);
    await setQuantity("0.3");
    await waitCart("$ 27,15");
  });

  await t.test("Admin descarga CSV del conjunto filtrado", async () => {
    await admin.goto(`${base}/admin/catalog/product/?q=Scroll&sale_unit__exact=unidad&is_active__exact=1`);
    const downloaded = admin.waitForEvent("download");
    await admin.getByRole("link", { name: "Exportar CSV", exact: true }).click();
    const download = await downloaded;
    const bytes = readFileSync(await download.path());
    assert.equal(bytes.subarray(0, 3).equals(Buffer.from([0xef, 0xbb, 0xbf])), true);
    const lines = bytes.toString("utf8").trim().split(/\r?\n/);
    assert.equal(lines.length, 11);
    assert.equal(lines.slice(1).every(line => line.includes("ZZZ QA Scroll") && line.endsWith(";Sí")), true);
  });

  await t.test("carrito largo conserva control, foco y scroll durante y después del recálculo", async () => {
    const isolated = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const scrolled = await isolated.newPage();
    await scrolled.goto(base);
    await scrolled.locator(".add-product").first().waitFor();
    await scrolled.locator(".add-product").evaluateAll(forms => {
      const items = forms.map(form => ({ id: Number(form.dataset.id), quantity: form.elements.quantity.value,
        price_type: "retail", sale_unit: form.dataset.unit, revision: form.dataset.revision }));
      localStorage.setItem("dulce-salado.cart.v1", JSON.stringify({ version: 1, items }));
    });
    await scrolled.goto(`${base}/carrito/`);
    await scrolled.locator(".total").waitFor();
    const input = scrolled.locator(".cart-quantity").nth(8);
    await input.evaluate(node => { node.scrollIntoView({ block: "center" }); node.focus({ preventScroll: true }); window.qaQuantityNode = node; });
    const before = await scrolled.evaluate(() => scrollY);
    assert.ok(before > 2000);
    let unblock, arrived;
    const release = new Promise(resolve => { unblock = resolve; });
    const requested = new Promise(resolve => { arrived = resolve; });
    await scrolled.route("**/carrito/recalcular/", async route => { arrived(); await release; await route.continue(); });
    try {
      await input.fill("2");
      await input.dispatchEvent("change");
      await requested;
      assert.equal(await input.isVisible(), true);
      assert.ok(Math.abs(await scrolled.evaluate(() => scrollY) - before) < 3);
      unblock();
      await scrolled.locator("#cart-contents[aria-busy]").waitFor({ state: "detached" });
      assert.ok(Math.abs(await scrolled.evaluate(() => scrollY) - before) < 3);
      assert.equal(await input.evaluate(node => node === window.qaQuantityNode && node === document.activeElement), true);
      assert.equal(Number(await input.inputValue()), 2);
      assert.match(await scrolled.locator(".total").innerText(), /46,13/);
      await scrolled.unrouteAll({ behavior: "wait" });
      const increase = scrolled.locator(".cart-item").nth(8).locator('[data-direction="1"]');
      await increase.evaluate(node => { node.focus({ preventScroll: true }); window.qaIncreaseNode = node; });
      await increase.press("Enter");
      await scrolled.locator(".total").filter({ hasText: "$ 47,13" }).waitFor();
      assert.equal(await increase.evaluate(node => node === window.qaIncreaseNode && node === document.activeElement), true);
      const pending = [];
      let firstArrived, secondArrived;
      const firstReady = new Promise(resolve => { firstArrived = resolve; });
      const secondReady = new Promise(resolve => { secondArrived = resolve; });
      await scrolled.route("**/carrito/recalcular/", async route => {
        const response = await route.fetch();
        let send;
        const gate = new Promise(resolve => { send = resolve; });
        pending.push({ send });
        if (pending.length === 1) firstArrived(); else secondArrived();
        await gate;
        await route.fulfill({ response });
      });
      try {
        await input.fill("4"); await input.dispatchEvent("change"); await firstReady;
        await input.fill("5"); await input.dispatchEvent("change"); await secondReady;
        pending[1].send();
        await scrolled.locator(".total").filter({ hasText: "$ 49,13" }).waitFor();
        const stale = scrolled.waitForResponse(response => response.url().endsWith("/carrito/recalcular/"));
        pending[0].send(); await stale;
        await scrolled.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        assert.match(await scrolled.locator(".total").innerText(), /49,13/);
        assert.equal(Number(await input.inputValue()), 5);
        assert.equal(await scrolled.locator("#cart-review").isEnabled(), true);
      } finally { pending.forEach(request => request.send()); await scrolled.unrouteAll({ behavior: "wait" }); }
      await scrolled.route("**/carrito/recalcular/", route => route.abort());
      await input.fill("6"); await input.dispatchEvent("change");
      await scrolled.getByText(/Los importes no se muestran/).waitFor();
      assert.equal(await input.isVisible(), true);
      assert.equal(await input.evaluate(node => node === window.qaQuantityNode), true);
      assert.equal(await scrolled.locator(".total").isVisible(), false);
      assert.equal(await scrolled.locator("#cart-review").isDisabled(), true);
      await scrolled.unrouteAll({ behavior: "wait" });
      await scrolled.getByRole("button", { name: "Reintentar" }).click();
      await scrolled.locator(".total").filter({ hasText: "$ 50,13" }).waitFor();
    } finally { unblock(); await isolated.close(); }
  });

  await t.test("mayorista retirado exige selección explícita", async () => {
    await editPrices("100.25", "");
    await page.reload();
    await page.getByText(/El precio mayorista ya no está disponible/).waitFor();
    assert.equal(await page.locator("#cart-review").isDisabled(), true);
    await page.locator(".cart-price").selectOption("retail");
    await waitCart("$ 30,08");
  });

  await t.test("diálogo accesible, Escape cancela, cambio posterior exige nueva revisión", async () => {
    await page.locator("#cart-review").click();
    await page.getByRole("dialog").waitFor();
    assert.equal(await page.locator("#review-title").evaluate(node => node === document.activeElement), true);
    await accessible();
    await page.screenshot({ path: ".qa/screenshots/review-mobile.png", fullPage: true });
    await page.keyboard.press("Escape");
    await page.getByRole("dialog").waitFor({ state: "hidden" });
    await page.waitForFunction(() => !document.getElementById("cart-review")?.disabled);
    assert.equal(await page.evaluate(() => document.activeElement?.id), "cart-review");
    await page.locator("#cart-review").click();
    await page.getByRole("dialog").waitFor();
    await editPrices("200.50", "90.50");
    await page.locator("#review-continue").click();
    await page.getByRole("dialog").getByText(/cambió la información/).waitFor();
    assert.equal(page.url(), `${base}/carrito/`);
    assert.match(await page.locator("#whatsapp-message").inputValue(), /Total estimado: \$ 60,15/);
  });

  await t.test("WhatsApp interceptado incluye mensaje completo; no envía ni borra carrito", async () => {
    let destination;
    await page.route(/^https:\/\/wa\.me\//, async route => {
      destination = route.request().url();
      await route.fulfill({ contentType: "text/html; charset=utf-8", body: "<h1>Salida interceptada de QA</h1>" });
    });
    await page.locator("#review-continue").click();
    await page.getByRole("heading", { name: "Salida interceptada de QA" }).waitFor();
    const url = new URL(destination);
    assert.equal(url.pathname, "/5491100000000");
    assert.match(url.searchParams.get("text"), /precio minorista \$ 200,50\/kg/);
    assert.match(url.searchParams.get("text"), /cantidad 0,3 kg/);
    assert.match(url.searchParams.get("text"), /Total estimado: \$ 60,15/);
    await page.goto(`${base}/carrito/`);
    await waitCart("$ 60,15");
  });

  await t.test("cancelar mientras se revalida impide salir a WhatsApp", async () => {
    let pending;
    const reached = new Promise(resolve => { pending = resolve; });
    let release;
    const released = new Promise(resolve => { release = resolve; });
    await page.route("**/carrito/whatsapp/", async route => {
      pending();
      await released;
      await route.continue();
    });
    await page.locator("#cart-review").click();
    await page.getByRole("dialog").waitFor();
    await page.locator("#review-continue").click();
    await reached;
    await page.locator("#review-cancel").click();
    await waitCart("$ 60,15");
    release();
    await page.waitForResponse(response => response.url().endsWith("/carrito/whatsapp/"));
    await page.unroute("**/carrito/whatsapp/");
    assert.equal(page.url(), `${base}/carrito/`);
    assert.equal(await page.getByRole("dialog").isVisible(), false);
  });

  await t.test("cambio de unidad exige cantidad nueva y sincroniza pestañas", async () => {
    await admin.goto(`${base}/admin/catalog/product/${chocolateId}/change/`);
    await admin.locator("#id_sale_unit").selectOption("unidad");
    await admin.locator("#id_quantity_step").fill("1");
    await admin.locator('input[name="_save"]').click();
    await page.reload();
    await page.getByText(/Cambió la unidad de venta/).waitFor();
    assert.equal(await page.locator(".cart-quantity").inputValue(), "");
    assert.equal(await page.locator("#cart-review").isDisabled(), true);
    await setQuantity("2");
    await waitCart("$ 401,00");
    const second = await context.newPage();
    await second.goto(`${base}/carrito/`);
    await second.locator(".total").filter({ hasText: "$ 401,00" }).waitFor();
    await setQuantity("3");
    await second.locator(".total").filter({ hasText: "$ 601,50" }).waitFor();
    await waitCart("$ 601,50");
    await second.close();
  });

  await t.test("fallo de red oculta importes, recuperación y producto retirado", async () => {
    await page.route("**/carrito/recalcular/", route => route.abort());
    await page.reload();
    await page.getByText(/Los importes no se muestran/).waitFor();
    assert.equal(await page.locator(".total").count(), 0);
    await page.unroute("**/carrito/recalcular/");
    await page.getByRole("button", { name: "Reintentar" }).click();
    await waitCart("$ 601,50");
    await admin.goto(`${base}/admin/catalog/product/${chocolateId}/change/`);
    await admin.locator("#id_is_active").uncheck();
    await admin.locator('input[name="_save"]').click();
    await page.reload();
    await page.getByText(/Este producto ya no está disponible/).waitFor();
    assert.equal(await page.locator("#cart-review").isDisabled(), true);
    await page.getByRole("button", { name: /Quitar producto/ }).click();
    await page.getByRole("heading", { name: "Tu carrito está vacío" }).waitFor();
  });

  await t.test("almacenamiento corrupto recuperable y sin errores JS", async () => {
    await page.evaluate(() => localStorage.setItem("dulce-salado.cart.v1", "invalid"));
    await page.reload();
    await page.getByText(/El carrito guardado no se pudo leer/).waitFor();
    await page.getByRole("button", { name: "Vaciar carrito" }).click();
    await page.getByRole("heading", { name: "Tu carrito está vacío" }).waitFor();
    assert.deepEqual(errors, []);
    await accessible();
  });

  await t.test("almacenamiento bloqueado informa y no habilita revisión", async () => {
    const blocked = await browser.newContext();
    await blocked.addInitScript(() => {
      Storage.prototype.setItem = function () { throw new DOMException("Test storage blocked", "QuotaExceededError"); };
    });
    const blockedPage = await blocked.newPage();
    await blockedPage.goto(base);
    await blockedPage.getByRole("button", { name: "Agregar al carrito" }).first().click();
    await blockedPage.getByText(/No se pudo guardar el carrito/).waitFor();
    await blockedPage.goto(`${base}/carrito/`);
    await blockedPage.getByRole("heading", { name: "Tu carrito está vacío" }).waitFor();
    assert.equal(await blockedPage.locator("#cart-review").count(), 0);
    await blocked.close();
  });

  await t.test("Cómo llegar sin dirección y configuración única desde Admin", async () => {
    await page.getByRole("link", { name: "Cómo llegar", exact: true }).click();
    await page.getByText(/La dirección del comercio todavía no está disponible/).waitFor();
    assert.equal(await page.getByRole("link", { name: "Abrir en Google Maps" }).count(), 0);
    await accessible();
    const address = "Dirección descartable de QA, no comercial";
    await admin.goto(`${base}/admin/catalog/businesssettings/add/`);
    await admin.locator("#id_address").fill(address);
    await admin.locator('input[name="_save"]').click();
    await admin.locator(".messagelist .success").waitFor();
    await page.reload();
    assert.equal(await page.locator("address").innerText(), address);
    const maps = page.getByRole("link", { name: "Abrir en Google Maps" });
    const link = new URL(await maps.getAttribute("href"));
    assert.equal(link.searchParams.get("query"), address);
    assert.equal(link.searchParams.get("api"), "1");
    for (const width of [360, 390, 430, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await page.screenshot({ path: `.qa/screenshots/directions-${width}.png`, fullPage: true });
    }
    await accessible();
    await page.route(/^https:\/\/www\.google\.com\/maps\//, route => route.fulfill({ contentType: "text/html", body: "<h1>Mapa interceptado de QA</h1>" }));
    await maps.click();
    await page.getByRole("heading", { name: "Mapa interceptado de QA" }).waitFor();
    await page.goto(`${base}/como-llegar/`);
  });

  await t.test("horario partido, validación Admin, desplegable y reloj local sin peticiones", async () => {
    await page.getByText("Horarios no disponibles", { exact: true }).waitFor();
    await admin.goto(`${base}/admin/catalog/businesssettings/1/change/`);
    await admin.locator("#id_hours_initialized").check();
    await admin.locator("#id_opening_intervals-0-weekday").selectOption("0");
    await admin.locator("#id_opening_intervals-0-opens_at").fill("09:00");
    await admin.locator("#id_opening_intervals-0-closes_at").fill("12:00");
    await admin.locator(".add-row a").click();
    await admin.locator("#id_opening_intervals-1-weekday").selectOption("0");
    await admin.locator("#id_opening_intervals-1-opens_at").fill("11:00");
    await admin.locator("#id_opening_intervals-1-closes_at").fill("15:00");
    await admin.locator('input[name="_save"]').click();
    await admin.getByText("Los intervalos de un mismo día no pueden superponerse.", { exact: true }).waitFor();
    await admin.locator("#id_opening_intervals-1-opens_at").fill("15:00");
    await admin.locator("#id_opening_intervals-1-closes_at").fill("18:00");
    await admin.locator('input[name="_save"]').click();
    await admin.locator(".messagelist .success").waitFor();
    await page.clock.install({ time: new Date("2026-10-12T14:59:50-03:00") });
    await page.reload();
    await page.locator("#business-status-text").filter({ hasText: "Cerrado" }).waitFor();
    let backgroundRequests = 0;
    page.on("request", request => { if (["fetch", "xhr"].includes(request.resourceType())) backgroundRequests++; });
    await page.clock.fastForward(20000);
    await page.locator("#business-status-text").filter({ hasText: "Abierto" }).waitFor();
    assert.equal(backgroundRequests, 0);
    assert.equal(await page.locator("#business-status-dot").evaluate(node => node.classList.contains("open")), true);
    await page.locator(".hours-panel summary").click();
    assert.equal(await page.locator(".weekly-hours > div").count(), 7);
    assert.match(await page.locator(".weekly-hours dd").first().innerText(), /09:00–12:00\s+15:00–18:00/);
    assert.equal(await page.locator(".weekly-hours dd").nth(1).innerText(), "Cerrado");
    for (const width of [360, 390, 430, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await page.screenshot({ path: `.qa/screenshots/hours-${width}.png`, fullPage: true });
    }
    await accessible();
    await page.locator(".hours-panel summary").press("Enter");
    assert.equal(await page.locator(".hours-panel").evaluate(node => node.open), false);
    const plain = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 360, height: 844 } });
    const plainPage = await plain.newPage();
    await plainPage.goto(`${base}/como-llegar/`);
    await plainPage.locator(".hours-panel summary").click();
    assert.equal(await plainPage.locator(".weekly-hours").isVisible(), true);
    await plain.close();
    assert.deepEqual(errors, []);
  });
});
