const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { chromium } = require("../.qa/node_modules/playwright");
const { default: AxeBuilder } = require("../.qa/node_modules/@axe-core/playwright");
const base = process.env.QA_BASE_URL || "http://127.0.0.1:8001";

test("Rediseño móvil: dos filas, categorías y carrito compartidos", { timeout: 120000 }, async t => {
  const browser = await chromium.launch();
  t.after(() => browser.close());
  const context = await browser.newContext({ viewport: { width: 320, height: 844 }, isMobile: true, hasTouch: true });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  const menu = page.locator(".mobile-categories");
  const trigger = menu.locator("summary");
  async function closed() { await page.waitForFunction(() => !document.querySelector(".mobile-categories").open); }
  async function accessible() {
    const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    assert.deepEqual(result.violations.map(item => ({ id: item.id, nodes: item.nodes.map(node => node.target) })), []);
  }
  // These fixtures remain independent of catalog edits made by earlier suites.
  const admin = await context.newPage();
  await admin.goto(`${base}/admin/login/`);
  await admin.locator("#id_username").fill("qa-admin");
  await admin.locator("#id_password").fill("qa-only-password-582");
  await admin.locator('input[type="submit"]').click();
  const products = [
    ["QA Mobile Chocolate con una presentación de nombre largo para comprobar dos líneas", "QA Repostería (test)", "QA Mobile Marca"],
    ["QA Mobile Velas", "QA Cotillón (test)", ""],
    ["QA Mobile ZZZ", "QA Repostería (test)", ""],
  ];
  for (const [name, category, brand] of products) {
    await admin.goto(`${base}/admin/catalog/product/add/`);
    await admin.locator("#id_category").selectOption({ label: category });
    await admin.locator("#id_name").fill(name);
    await admin.locator("#id_brand").fill(brand);
    await admin.locator("#id_description").fill("Presentación de prueba con texto secundario para comprobar alineación.");
    await admin.locator("#id_retail_price").fill("100");
    await admin.locator("#id_image").setInputFiles({ name: "qa-mobile.webp", mimeType: "image/webp", buffer: readFileSync("static/img/logo.webp") });
    await admin.locator('input[name="_save"]').click();
    await admin.locator(".messagelist .success").waitFor();
  }
  await admin.close();
  await page.goto(`${base}/?q=QA%20Mobile`);

  await t.test("320/360/375/390/430 px: filas alineadas, controles e imágenes completas", async () => {
    const card = page.locator(".product-card").first();
    await card.locator(".catalog-increase").click();
    await card.locator(".catalog-amount").fill("9999999");
    await card.locator(".catalog-amount").press("Tab");
    for (const width of [320, 360, 375, 390, 430]) {
      await page.setViewportSize({ width, height: 844 });
      const layout = await page.evaluate(() => {
        const box = selector => document.querySelector(selector).getBoundingClientRect().toJSON();
        const first = box(".product-card"), controls = [...document.querySelector(".product-card").querySelectorAll("button, input")].filter(node => !node.hidden).map(node => node.getBoundingClientRect());
        return { first, second: document.querySelectorAll(".product-card")[1].getBoundingClientRect().toJSON(),
          logo: box(".brand-logo"), search: box(".search-form"), cart: box(".cart-link"), info: box(".header-info"),
          header: box("header"), title: getComputedStyle(document.querySelector(".brand > span")).display,
          count: document.querySelectorAll("header .cart-link").length,
          scroll: document.documentElement.scrollWidth > innerWidth,
          controlsFit: controls.every(control => control.left >= first.left && control.right <= first.right && control.bottom <= first.bottom),
          buttonsTouch: controls.filter(control => control.width === 44).length >= 2,
          fit: getComputedStyle(document.querySelector(".product-image img")).objectFit };
      });
      assert.equal(layout.scroll, false);
      assert.equal(layout.title, "none");
      assert.equal(layout.count, 1);
      assert.equal(layout.logo.width, 40);
      assert.ok(layout.search.height >= 34 && layout.search.height <= 38);
      assert.ok(layout.header.height <= 104);
      assert.ok(layout.logo.right <= layout.search.left && layout.search.right <= layout.cart.left);
      assert.ok(layout.info.top >= layout.logo.bottom);
      assert.equal(layout.first.top, layout.second.top);
      assert.ok(Math.abs(layout.first.height - layout.second.height) < 1);
      assert.ok(layout.controlsFit && layout.buttonsTouch);
      assert.equal(layout.fit, "contain");
      const mainTop = await page.locator("main").evaluate(node => node.getBoundingClientRect().top);
      await trigger.click();
      const panel = await page.locator(".category-menu").boundingBox();
      assert.ok(panel.x >= 0 && panel.x + panel.width <= width);
      assert.equal(await page.locator("main").evaluate(node => node.getBoundingClientRect().top), mainTop);
      await page.keyboard.press("Escape");
      await closed();
      await page.screenshot({ path: `.qa/screenshots/mobile-redesign-${width}.png` });
    }
    await card.locator(".catalog-amount").fill("1");
    await card.locator(".catalog-amount").press("Tab");
    await card.locator(".catalog-decrease").click();
  });

  await t.test("buscador enfoca al tocar, acepta Enter/lupa y permite limpiar", async () => {
    const search = page.locator("#catalog-search");
    await search.tap();
    assert.equal(await search.evaluate(node => document.activeElement === node), true);
    await search.fill("QA Mobile Marca");
    await search.press("Enter");
    await page.waitForURL(url => url.searchParams.get("q") === "QA Mobile Marca");
    assert.equal(await page.locator(".product-card").count(), 1);
    await search.fill("");
    await page.getByRole("button", { name: "Buscar", exact: true }).click();
    await page.waitForURL(url => url.searchParams.get("q") === "");
    assert.ok(await page.locator(".product-card").count() > 1);
  });

  await t.test("categorías: apertura explícita, Escape/foco, exterior y selección GET", async () => {
    const mainTop = await page.locator("main").evaluate(node => node.getBoundingClientRect().top);
    await trigger.hover();
    assert.equal(await menu.evaluate(node => node.open), false);
    await trigger.press("Enter");
    await page.locator(".category-menu").waitFor();
    assert.equal(await page.locator("main").evaluate(node => node.getBoundingClientRect().top), mainTop);
    await accessible();
    await page.keyboard.press("Escape");
    await closed();
    assert.equal(await trigger.evaluate(node => document.activeElement === node), true);
    await trigger.press("Space");
    await page.locator("#catalog-search").tap();
    await closed();
    await page.locator("#catalog-search").fill("QA Mobile");
    await page.locator("#catalog-search").press("Enter");
    await page.waitForURL(url => url.searchParams.get("q") === "QA Mobile");
    await trigger.click();
    await menu.getByRole("link", { name: "QA Cotillón (test)", exact: true }).click();
    await page.waitForURL(url => url.searchParams.get("categoria") === "qa-cotillon");
    await closed();
    assert.equal(new URL(page.url()).searchParams.get("q"), "QA Mobile");
    assert.equal(await trigger.getAttribute("aria-label"), "Categorías: QA Cotillón (test)");
    await trigger.click();
    assert.equal(await menu.locator('a[aria-current="page"]').innerText(), "QA Cotillón (test)");
    await menu.getByRole("link", { name: "Todas las categorías", exact: true }).click();
    await page.waitForURL(url => !url.searchParams.has("categoria"));
    await accessible();
  });

  await t.test("cantidad editable, suma/resta, iframe, total y eliminación sincronizados", async () => {
    const card = page.locator(".product-card").first();
    await card.locator(".catalog-increase").click();
    await card.locator(".catalog-increase").click();
    assert.equal(await card.locator(".catalog-amount").inputValue(), "2");
    await card.locator(".catalog-decrease").click();
    assert.equal(await card.locator(".catalog-amount").inputValue(), "1");
    await card.locator(".catalog-amount").fill("3");
    await card.locator(".catalog-amount").press("Tab");
    await page.locator(".cart-link").click();
    const frame = page.frameLocator("#cart-drawer iframe");
    const quantity = frame.locator(".cart-quantity");
    await quantity.waitFor();
    assert.equal(await quantity.inputValue(), "3");
    assert.match(await frame.locator(".total").innerText(), /\$/);
    await quantity.fill("2");
    await quantity.press("Tab");
    await page.waitForFunction(() => document.querySelector(".catalog-amount").value === "2");
    await page.locator(".cart-drawer-close").click();
    await card.locator(".catalog-amount").fill("1");
    await card.locator(".catalog-amount").press("Tab");
    await card.locator(".catalog-decrease").click();
    assert.equal(await card.locator(".catalog-amount").isVisible(), false);
    assert.equal(await page.locator("[data-cart-count]").innerText(), "0");
  });

  await t.test("sin JavaScript: categorías y búsqueda conservan navegación nativa", async () => {
    const plain = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 320, height: 844 } });
    const fallback = await plain.newPage();
    await fallback.goto(`${base}/?q=QA%20Mobile`);
    await fallback.locator(".mobile-categories summary").click();
    await fallback.locator(".category-menu").getByRole("link", { name: "QA Cotillón (test)", exact: true }).click();
    await fallback.waitForURL(url => url.searchParams.get("categoria") === "qa-cotillon");
    await fallback.locator("#catalog-search").fill("Velas");
    await fallback.locator("#catalog-search").press("Enter");
    await fallback.waitForURL(url => url.searchParams.get("q") === "Velas");
    assert.equal(new URL(fallback.url()).searchParams.get("categoria"), "qa-cotillon");
    assert.ok(await fallback.locator(".product-card").count() > 0);
    assert.equal(await fallback.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await plain.close();
  });
  assert.deepEqual(errors, []);
});
