const test = require("node:test");
const assert = require("node:assert/strict");
const { chromium } = require("../.qa/node_modules/playwright");
const { default: AxeBuilder } = require("../.qa/node_modules/@axe-core/playwright");
const base = process.env.QA_BASE_URL || "http://127.0.0.1:8001";
const key = "dulce-salado.cart.v1";

test("Pedidos persistidos: datos, errores, resultado, reenvío y privacidad", { timeout: 180000 }, async t => {
  const browser = await chromium.launch();
  t.after(() => browser.close());
  async function setup(panel = false, width = 390) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    const page = await context.newPage(), errors = [], destinations = [];
    page.on("pageerror", error => errors.push(error.message));
    await context.route("https://api.whatsapp.com/**", async route => {
      destinations.push(route.request().url());
      await route.fulfill({ contentType: "text/html; charset=utf-8", body: "<h1>WhatsApp QA sin envío real</h1>" });
    });
    await page.goto(base);
    const product = page.locator(".add-product").first();
    const id = await product.getAttribute("data-id");
    await product.locator(".catalog-increase").click();
    await page.evaluate(() => Notifications.close());
    let cart = page;
    if (panel) { await page.locator(".cart-link").click(); cart = page.frameLocator("#cart-drawer iframe"); }
    else await page.goto(`${base}/carrito/`);
    await cart.locator("#cart-review:not([disabled])").waitFor();
    await cart.locator("#cart-review").click();
    await cart.locator("#id_full_name").waitFor();
    return { context, page, cart, errors, destinations, id };
  }
  async function stored(page) { return page.evaluate(key => JSON.parse(localStorage.getItem(key)).items, key); }
  async function send(state) {
    const popup = state.context.waitForEvent("page");
    await state.cart.locator("#review-continue").click();
    const opened = await popup;
    await state.page.locator("#order-result-dialog[open]").waitFor();
    await opened.getByRole("heading", { name: "WhatsApp QA sin envío real" }).waitFor();
    return opened;
  }

  await t.test("nombre, radios reales, dirección condicional y conservación al cancelar", async () => {
    const s = await setup();
    try {
      assert.equal(await s.cart.locator("#review-title").innerText(), "Completá tus datos");
      assert.equal(await s.cart.locator("textarea, #copy-message").count(), 0);
      assert.equal(await s.cart.locator('input[name="delivery_mode"][value="pickup"]').isChecked(), true);
      assert.equal(await s.cart.locator("#delivery-address").isVisible(), false);
      assert.equal(await s.cart.locator("#id_city").inputValue(), "Viedma");
      let writes = 0;
      s.page.on("request", request => { if (request.url().endsWith("/carrito/whatsapp/")) writes++; });
      await s.cart.locator("#id_full_name").fill("   ");
      await s.cart.locator("#review-continue").click();
      assert.match(await s.cart.locator("#id_full_name_error").innerText(), /Completá/);
      assert.equal(writes, 0);
      await s.cart.locator("#id_full_name").fill("Ana");
      await s.cart.locator('input[value="delivery"]').check();
      assert.equal(await s.cart.locator('input[value="pickup"]').isChecked(), false);
      await s.cart.locator("#review-continue").click();
      assert.match(await s.cart.locator("#id_street_error").innerText(), /Completá/);
      assert.match(await s.cart.locator("#id_number_error").innerText(), /Completá/);
      assert.equal(writes, 0);
      await s.cart.locator("#id_street").fill("San Martín");
      await s.cart.locator("#id_number").fill("123");
      await s.cart.locator("#id_city").fill("Patagones");
      await s.cart.locator('input[value="pickup"]').check();
      assert.equal(await s.cart.locator("#id_street").isDisabled(), true);
      await s.cart.locator('input[value="delivery"]').check();
      assert.equal(await s.cart.locator("#id_street").inputValue(), "San Martín");
      await s.cart.locator("#review-cancel").click();
      await s.cart.locator("#cart-review:not([disabled])").waitFor();
      await s.cart.locator("#cart-review").click();
      await s.cart.locator("#id_full_name").waitFor();
      assert.equal(await s.cart.locator("#id_full_name").inputValue(), "Ana");
      assert.equal(await s.cart.locator("#id_city").inputValue(), "Patagones");
      assert.equal((await stored(s.page)).length, 1);
      assert.equal(writes, 0);
    } finally { await s.context.close(); }
  });

  for (const panel of [false, true]) for (const width of [320, 390, 768, 1280]) {
    await t.test(`${panel ? "iframe" : "carrito"} ${width}px: persiste, vacía, detalle y reenvío idéntico`, async () => {
      const s = await setup(panel, width);
      try {
        await s.cart.locator("#id_full_name").fill("Ana QA á & ñ");
        const delivery = width === 390 || width === 1280;
        if (delivery) {
          await s.cart.locator('input[value="delivery"]').check();
          await s.cart.locator("#id_street").fill("San Martín");
          await s.cart.locator("#id_number").fill("123");
        }
        assert.equal(await s.cart.locator('[name="door"]').count(), 0);
        const cta = await s.cart.locator("#cart-review").evaluate(n => ({gap: parseFloat(getComputedStyle(n).gap),
          width: n.querySelector("svg").getBoundingClientRect().width, display: getComputedStyle(n).display}));
        assert.ok(cta.gap >= 8 && cta.gap <= 10 && cta.width >= 22 && cta.width <= 24);
        assert.equal(cta.display, "inline-flex");
        const radios = await s.cart.locator('.delivery-options label').evaluateAll(nodes => nodes.map(n => n.getBoundingClientRect().toJSON()));
        assert.ok(Math.abs(radios[0].top - radios[1].top) < 1 && radios[0].right < radios[1].left);
        if (delivery) {
          const street = await s.cart.locator("#id_street").boundingBox();
          const number = await s.cart.locator("#id_number").boundingBox();
          const city = await s.cart.locator("#id_city").boundingBox();
          assert.equal(street.y, number.y);
          assert.ok(street.width > number.width * 2.8 && city.y > street.y);
        }
        const axe = await new AxeBuilder({ page: s.page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
        assert.deepEqual(axe.violations.map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) })), []);
        assert.equal(await s.cart.locator("body").evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
        await s.page.screenshot({ path: `.qa/screenshots/order-${panel ? "iframe" : "page"}-${width}.png` });
        const other = await s.context.newPage();
        await other.goto(base);
        assert.equal(await other.locator("[data-cart-count]").first().innerText(), "1");
        await s.page.bringToFront();
        const popup = await send(s);
        assert.equal(await popup.evaluate(() => opener), null);
        assert.equal(await popup.evaluate(() => document.referrer), "");
        const original = s.destinations.at(-1);
        const message = new URL(original).searchParams.get("text");
        assert.match(message, /Pedido: DYS-\d+/);
        assert.match(message, /Nombre completo: Ana QA á & ñ/);
        if (delivery) {
          assert.match(message, /Calle: San Martín\nNúmero: 123\nCiudad: Viedma/);
          assert.ok(!message.includes("Puerta:"));
        } else assert.ok(!message.includes("Calle:"));
        assert.deepEqual(await stored(s.page), []);
        await other.waitForFunction(() => document.querySelector("[data-cart-count]").textContent === "0");
        const detailUrl = message.split("\n").at(-1);
        assert.equal(await s.page.locator("#order-detail-link").count(), 0);
        assert.equal(await s.page.locator("#order-result-title").innerText(), "¡Tu pedido fue generado con éxito! 🎉");
        assert.deepEqual(await s.page.locator("#order-result-body p").allTextContents(), [
          "Tu pedido ha sido generado correctamente.",
          "Si WhatsApp no se abrió automáticamente, podés intentar enviarlo nuevamente."
        ]);
        assert.equal(await s.page.locator("#order-result-dialog a, #order-result-dialog button").count(), 2);
        const modal = await s.page.locator("#order-result-dialog").boundingBox();
        assert.ok(Math.abs(modal.x + modal.width / 2 - width / 2) < 2);
        assert.ok(Math.abs(modal.y + modal.height / 2 - 450) < 2);
        const actions = await s.page.locator(".order-result-actions > *").evaluateAll(nodes => nodes.map(n => n.getBoundingClientRect().toJSON()));
        assert.ok(Math.abs(actions[0].width - actions[1].width) < 1 && actions[0].height === actions[1].height);
        assert.ok(actions[0].right < actions[1].left && actions[0].top === actions[1].top);
        if (width >= 768) assert.ok(actions[0].width <= 152);
        if (panel) {
          assert.equal(await s.page.locator("#cart-drawer").evaluate(node => node.open), false);
          assert.equal(await s.page.locator("#cart-drawer #order-result-dialog").count(), 0);
          assert.equal(s.page.frames().some(f => f.url().includes("panel=1")), false);
        }
        const resultAxe = await new AxeBuilder({ page: s.page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
        assert.deepEqual(resultAxe.violations.map(v => v.id), []);
        await s.page.screenshot({ path: `.qa/screenshots/order-result-${panel ? "iframe" : "page"}-${width}.png` });
        assert.match(detailUrl, /\/orders\/[0-9a-f-]{36}\/$/);
        assert.ok(message.includes(detailUrl));
        const response = await s.context.request.get(detailUrl);
        assert.equal(response.status(), 200);
        assert.match(response.headers()["cache-control"], /no-store/);
        assert.match(response.headers()["x-robots-tag"], /noindex/);
        const detail = await s.context.newPage();
        await detail.goto(detailUrl);
        assert.match(await detail.locator("h1").innerText(), /DYS-/);
        assert.equal(await detail.locator("header").count(), 0);
        assert.equal(await detail.locator(".order-detail .brand-logo").count(), 1);
        const card = await detail.locator(".order-detail").boundingBox();
        assert.ok(card.width <= 860 && Math.abs(card.x + card.width / 2 - width / 2) < 1);
        if (card.height < 868) assert.ok(Math.abs(card.y + card.height / 2 - 450) < 1);
        await detail.screenshot({ path: `.qa/screenshots/order-detail-${panel ? "iframe" : "page"}-${width}.png` });
        const detailAxe = await new AxeBuilder({ page: detail }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
        assert.deepEqual(detailAxe.violations.map(v => v.id), []);
        assert.equal(await detail.locator("body").evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
        // The same row structure must grow naturally for a long order.
        await detail.locator(".order-products").evaluate(list => {
          const row = list.firstElementChild;
          for (let i = 0; i < 30; i++) list.append(row.cloneNode(true));
        });
        assert.ok((await detail.locator(".order-detail").boundingBox()).y >= 16);
        await detail.locator(".order-privacy").scrollIntoViewIfNeeded();
        assert.ok(await detail.evaluate(() => scrollY > 0 && document.querySelector(".order-privacy").getBoundingClientRect().bottom <= innerHeight));
        await detail.close(); await popup.close();
        const resend = s.context.waitForEvent("page");
        await s.page.locator("#whatsapp-ready").click();
        const manual = await resend;
        await manual.getByRole("heading", { name: "WhatsApp QA sin envío real" }).waitFor();
        assert.equal(s.destinations.at(-1), original);
        assert.deepEqual(await stored(s.page), []);
        await manual.close();
        await s.page.locator("#order-result-close").click();
        if (panel) {
          assert.equal(await s.page.locator(".cart-link").evaluate(node => document.activeElement === node), true);
        } else await s.page.waitForURL(`${base}/#contenido`);
        await s.page.locator(".product-card").first().waitFor();
        await s.page.locator(".cart-link").click();
        const empty = s.page.frameLocator("#cart-drawer iframe");
        await empty.locator(".empty-state").waitFor();
        assert.equal(await empty.locator(".empty-state").count(), 1);
        assert.deepEqual(s.errors, []);
      } finally { await s.context.close(); }
    });
  }

  await t.test("popup bloqueado: enlace manual seguro sin otro POST", async () => {
    const s = await setup(true);
    try {
      await s.cart.locator("#id_full_name").fill("Ana popup QA");
      const frame = s.page.frames().find(frame => frame.url().includes("panel=1"));
      await frame.evaluate(() => { window.open = () => null; });
      let posts = 0;
      s.page.on("request", r => { if (r.url().endsWith("/carrito/whatsapp/")) posts++; });
      await s.cart.locator("#review-continue").click();
      await s.page.locator("#order-result-dialog[open]").waitFor();
      assert.equal(posts, 1);
      const link = s.page.locator("#whatsapp-ready");
      assert.equal(await link.getAttribute("rel"), "noopener noreferrer");
      const opening = s.context.waitForEvent("page"); await link.click();
      const popup = await opening;
      await popup.getByRole("heading", { name: "WhatsApp QA sin envío real" }).waitFor();
      assert.equal(posts, 1);
      assert.deepEqual(await stored(s.page), []);
    } finally { await s.context.close(); }
  });

  await t.test("doble clic y Escape durante escritura no duplican ni abandonan la operación", async () => {
    const s = await setup();
    let release;
    try {
      await s.cart.locator("#id_full_name").fill("Ana doble QA");
      const gate = new Promise(resolve => { release = resolve; });
      let posts = 0, arrived;
      const received = new Promise(resolve => { arrived = resolve; });
      await s.page.route("**/carrito/whatsapp/", async route => { posts++; arrived(); await gate; await route.continue(); });
      const opening = s.context.waitForEvent("page");
      await s.cart.locator("#review-continue").evaluate(button => { button.click(); button.click(); });
      const popup = await opening; await received;
      assert.equal(await s.cart.locator("#review-cancel").isDisabled(), true);
      await s.page.keyboard.press("Escape");
      assert.equal(await s.cart.locator("#cart-review-dialog").evaluate(node => node.open), true);
      assert.equal((await stored(s.page)).length, 1);
      release();
      await s.page.locator("#order-result-dialog[open]").waitFor();
      assert.equal(posts, 1);
      assert.deepEqual(await stored(s.page), []);
      await popup.close();
    } finally { release?.(); await s.context.close(); }
  });

  await t.test("respuesta perdida después de persistir: recupera el mismo código sin vaciar antes", async () => {
    const s = await setup();
    let savedCode, requests = [];
    try {
      await s.cart.locator("#id_full_name").fill("Ana red QA");
      await s.page.route("**/carrito/whatsapp/", async route => {
        requests.push(route.request().postData());
        const result = await route.fetch();
        savedCode = (await result.text()).match(/data-code="(DYS-\d+)"/)[1];
        await route.abort();
      });
      const opening = s.context.waitForEvent("page");
      await s.cart.locator("#review-continue").click();
      const provisional = await opening;
      await s.cart.locator("#id_full_name:disabled").waitFor();
      if (!provisional.isClosed()) await provisional.waitForEvent("close");
      assert.equal((await stored(s.page)).length, 1);
      assert.equal(await s.cart.locator("#id_full_name").inputValue(), "Ana red QA");
      assert.equal(await s.page.locator("#order-result-dialog[open]").count(), 0);
      await s.page.unroute("**/carrito/whatsapp/");
      s.page.on("request", r => { if (r.url().endsWith("/carrito/whatsapp/")) requests.push(r.postData()); });
      const popup = await send(s);
      assert.equal(await s.page.locator("#order-result-dialog").getAttribute("data-code"), savedCode);
      // FormData boundaries pueden variar; la clave firmada y todos los valores permanecen iguales.
      const values = raw => [...raw.matchAll(/name="([^"]+)"\r\n\r\n([^\r]*)/g)].map(m => [m[1], m[2]]);
      assert.deepEqual(values(requests[0]), values(requests[1]));
      assert.deepEqual(await stored(s.page), []);
      await popup.close();
    } finally { await s.context.close(); }
  });

  await t.test("error 500 conserva carrito y datos; otra pestaña conserva modificaciones durante envío", async () => {
    const s = await setup();
    try {
      await s.cart.locator("#id_full_name").fill("Ana cambios QA");
      await s.page.route("**/carrito/whatsapp/", route => route.fulfill({ status: 500, body: "QA" }));
      const opening = s.context.waitForEvent("page"); await s.cart.locator("#review-continue").click();
      const failed = await opening;
      await s.cart.locator("#id_full_name:disabled").waitFor();
      if (!failed.isClosed()) await failed.waitForEvent("close");
      assert.equal((await stored(s.page)).length, 1);
      await s.page.unroute("**/carrito/whatsapp/");
      const other = await s.context.newPage(); await other.goto(base);
      await other.evaluate(key => {
        const data = JSON.parse(localStorage.getItem(key)); data.items[0].quantity = "4";
        localStorage.setItem(key, JSON.stringify(data));
      }, key);
      await s.page.bringToFront();
      await s.cart.locator("#cart-review-dialog[open]").waitFor({ state: "hidden" });
      await s.cart.locator("#cart-review:not([disabled])").waitFor();
      await s.cart.locator("#cart-review").click();
      const popup = await send(s);
      assert.equal((await stored(s.page))[0].quantity, "4");
      assert.deepEqual(s.errors, []);
      await popup.close();
    } finally { await s.context.close(); }
  });
  await t.test("iframe: rechaza mensajes de otro origen, otra ventana y destinos no permitidos", async () => {
    const s = await setup(true);
    try {
      await s.page.evaluate(() => {
        const frame = document.querySelector("#cart-drawer iframe").contentWindow;
        const data = { type: "dys-order-complete", code: "DYS-000001", url: "https://api.whatsapp.com/send?phone=5492920000000&text=QA" };
        window.dispatchEvent(new MessageEvent("message", { origin: "https://otro.example", source: frame, data }));
        window.dispatchEvent(new MessageEvent("message", { origin: location.origin, source: window, data }));
        window.dispatchEvent(new MessageEvent("message", { origin: location.origin, source: frame,
          data: { ...data, url: "javascript:alert(1)" } }));
      });
      assert.equal(await s.page.locator("#cart-drawer").evaluate(n => n.open), true);
      assert.equal(await s.page.locator("#order-result-dialog").evaluate(n => n.open), false);
      assert.equal((await stored(s.page)).length, 1);
    } finally { await s.context.close(); }
  });

  await t.test("limpieza fallida: informa guardado, conserva selección y reintenta sin otro POST", async () => {
    const s = await setup(true);
    try {
      await s.cart.locator("#id_full_name").fill("Ana almacenamiento QA");
      const frame = s.page.frames().find(f => f.url().includes("panel=1"));
      await frame.evaluate(() => {
        window.__qaWrite = Storage.prototype.setItem;
        Storage.prototype.setItem = function (key, value) {
          if (key === "dulce-salado.cart.v1") throw new DOMException("QA", "QuotaExceededError");
          return window.__qaWrite.call(this, key, value);
        };
      });
      let posts = 0;
      s.page.on("request", r => { if (r.url().endsWith("/carrito/whatsapp/")) posts++; });
      const opening = s.context.waitForEvent("page");
      await s.cart.locator("#review-continue").click();
      const popup = await opening;
      await s.cart.locator("#cart-clear-error:not([hidden])").waitFor();
      assert.match(await s.cart.locator("#cart-clear-error").innerText(), /pedido ya está guardado/);
      assert.equal(await s.page.locator("#cart-drawer").evaluate(n => n.open), true);
      assert.equal(await s.page.locator("#order-result-dialog").evaluate(n => n.open), false);
      assert.equal((await stored(s.page)).length, 1);
      await s.cart.locator("#retry-cart-clear").click();
      assert.equal(posts, 1);
      await frame.evaluate(() => { Storage.prototype.setItem = window.__qaWrite; });
      await s.cart.locator("#retry-cart-clear").click();
      await s.page.locator("#order-result-dialog[open]").waitFor();
      assert.equal(posts, 1);
      assert.deepEqual(await stored(s.page), []);
      assert.equal(popup.isClosed(), false);
      await s.page.keyboard.press("Tab");
      assert.equal(await s.page.locator("#whatsapp-ready").evaluate(n => document.activeElement === n), true);
      await s.page.keyboard.press("Tab");
      assert.equal(await s.page.locator("#order-result-close").evaluate(n => document.activeElement === n), true);
      await s.page.keyboard.press("Enter");
      assert.equal(await s.page.locator(".cart-link").evaluate(n => document.activeElement === n), true);
    } finally { await s.context.close(); }
  });

  await t.test("iframe: vacío repetido, pestañas, nuevos artículos y cantidades con control conectado", async () => {
    const s = await setup(true);
    try {
      await s.cart.locator("#review-cancel").click();
      const other = await s.context.newPage(); await other.goto(base);
      const selection = await stored(s.page);
      async function update(items) {
        const response = s.page.waitForResponse(r => r.url().endsWith("/carrito/recalcular/"));
        await other.evaluate(({key, items}) => localStorage.setItem(key, JSON.stringify({ version: 1, items })), {key, items});
        await response;
        await s.cart.locator("#cart-contents:not([aria-busy])").waitFor();
      }
      await update([]);
      for (let i = 0; i < 8; i++) {
        // Distinct storage values trigger genuine cross-document events for the same empty cart.
        const response = s.page.waitForResponse(r => r.url().endsWith("/carrito/recalcular/"));
        await other.evaluate(({key, i}) => localStorage.setItem(key, JSON.stringify({version: 1, items: [], qa: i})), {key, i});
        await response;
        await s.cart.locator("#cart-contents:not([aria-busy])").waitFor();
        assert.equal(await s.cart.locator(".empty-state").count(), 1);
        assert.equal(await s.cart.locator(".cart-item").count(), 0);
      }
      await update(selection);
      assert.equal(await s.cart.locator(".empty-state").count(), 0);
      await s.cart.locator(".cart-quantity").evaluate(n => { window.__qaControl = n; });
      await s.cart.locator(".cart-adjust[data-direction='1']").click();
      await s.cart.locator("#cart-contents:not([aria-busy]) #cart-review:not([disabled])").waitFor();
      assert.equal(await s.cart.locator(".cart-quantity").evaluate(n => n === window.__qaControl && n.isConnected), true);
      assert.equal(await s.cart.locator(".cart-quantity").inputValue(), "2");
      await update([]);
      assert.equal(await s.cart.locator(".empty-state").count(), 1);
      assert.deepEqual(s.errors, []);
    } finally { await s.context.close(); }
  });

  await t.test("rechazo desde iframe conserva panel, carrito y formulario sin mostrar éxito", async () => {
    const s = await setup(true);
    try {
      await s.cart.locator("#id_full_name").fill("Ana rechazo QA");
      await s.context.route("**/carrito/whatsapp/", route => route.fulfill({status: 500, body: "QA"}));
      const opening = s.context.waitForEvent("page");
      await s.cart.locator("#review-continue").click();
      const popup = await opening;
      await s.cart.locator("#id_full_name:disabled").waitFor();
      if (!popup.isClosed()) await popup.waitForEvent("close");
      assert.equal(await s.page.locator("#cart-drawer").evaluate(n => n.open), true);
      assert.equal(await s.page.locator("#order-result-dialog").evaluate(n => n.open), false);
      assert.equal(await s.cart.locator("#id_full_name").inputValue(), "Ana rechazo QA");
      assert.equal((await stored(s.page)).length, 1);
    } finally { await s.context.close(); }
  });

});
