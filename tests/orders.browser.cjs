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
    await state.cart.locator("#order-result").waitFor();
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
        const detailUrl = await s.cart.locator("#order-detail-link").getAttribute("href");
        assert.match(detailUrl, /\/orders\/[0-9a-f-]{36}\/$/);
        assert.ok(message.includes(detailUrl));
        const response = await s.context.request.get(detailUrl);
        assert.equal(response.status(), 200);
        assert.match(response.headers()["cache-control"], /no-store/);
        assert.match(response.headers()["x-robots-tag"], /noindex/);
        const detail = await s.context.newPage();
        await detail.goto(detailUrl);
        assert.match(await detail.locator("h1").innerText(), /DYS-/);
        assert.equal(await detail.locator("body").evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
        await detail.close(); await popup.close();
        const resend = s.context.waitForEvent("page");
        await s.cart.locator("#whatsapp-ready").click();
        const manual = await resend;
        await manual.getByRole("heading", { name: "WhatsApp QA sin envío real" }).waitFor();
        assert.equal(s.destinations.at(-1), original);
        assert.deepEqual(await stored(s.page), []);
        await manual.close();
        await s.cart.locator("#review-cancel").click();
        await s.cart.locator(".empty-state").waitFor();
        assert.equal(await s.cart.locator("#cart-review-dialog").evaluate(node => node.open), false);
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
      await s.cart.locator("#order-result").waitFor();
      assert.equal(posts, 1);
      const link = s.cart.locator("#whatsapp-ready");
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
      await s.cart.locator("#order-result").waitFor();
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
      assert.equal(await s.cart.locator("#order-result").count(), 0);
      await s.page.unroute("**/carrito/whatsapp/");
      s.page.on("request", r => { if (r.url().endsWith("/carrito/whatsapp/")) requests.push(r.postData()); });
      const popup = await send(s);
      assert.equal(await s.cart.locator("#order-result").getAttribute("data-code"), savedCode);
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
});
