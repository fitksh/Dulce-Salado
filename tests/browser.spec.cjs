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
  // Recurso externo independiente de QA: el test sólo inspecciona el iframe/atributos.
  await context.route("https://www.google.com/maps/embed?*", route => route.fulfill({ contentType: "text/html", body: '<p>Mapa aislado de QA</p><button onclick="this.textContent=\'Mapa interactuado\'">Interactuar con mapa de QA</button>' }));
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
  async function headerLayout(width) {
    const regions = await page.locator(".header-inner").evaluate(node => [".brand", ".business-hours", ".header-actions"].map(selector => {
      const r = node.querySelector(selector).getBoundingClientRect();
      return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2 };
    }));
    assert.ok(regions.every(r => r.left >= 16 && r.right <= width - 16));
    if (width >= 800) {
      assert.ok(regions.every(r => Math.abs(r.y - regions[0].y) < 2));
      assert.ok(regions[0].right <= regions[1].left && regions[1].right <= regions[2].left);
    } else {
      assert.ok(regions.every(r => Math.abs(r.x - width / 2) < 2));
      assert.ok(regions[0].bottom <= regions[1].top && regions[1].bottom <= regions[2].top);
    }
  }
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
    assert.equal(await page.locator(".wholesale-note").count(), 1);
    assert.equal(await page.locator(".wholesale-note").evaluate(node => getComputedStyle(node).backgroundColor), "rgb(255, 240, 246)");
    assert.equal(await page.getByText("QA Invisible").count(), 0);
    for (const width of [320, 360, 390, 430, 768, 800, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await headerLayout(width);
      assert.equal(await page.locator(".brand-logo").evaluate(node => node.getBoundingClientRect().width), 64);
      const actions = await page.locator(".header-actions a").evaluateAll(nodes => nodes.map(node => node.getBoundingClientRect().toJSON()));
      assert.equal(actions.length, 3);
      assert.ok(Math.abs(actions[0].top - actions[1].top) < 1);
      assert.ok(Math.abs(actions[1].top - actions[2].top) < 1);
      assert.ok(Math.abs(actions[0].width - actions[1].width) < 1);
      assert.equal(await page.locator('.header-actions a[aria-current="page"]').getAttribute("href"), "/");
      const targets = await page.locator("button, input:not([type=hidden]), select, .button, .chip").evaluateAll(nodes => nodes.filter(n => n.getBoundingClientRect().height > 0).map(n => ({ tag: n.tagName, height: n.getBoundingClientRect().height })));
      assert.equal(targets.every(target => target.height >= 44), true, JSON.stringify(targets));
      const steppers = await page.locator(".quantity-adjust").evaluateAll(nodes => nodes.map(n => n.getBoundingClientRect().width));
      assert.equal(steppers.every(width => width >= 44), true);
      await page.screenshot({ path: `.qa/screenshots/catalog-${width}.png`, fullPage: true });
      await page.screenshot({ path: `.qa/screenshots/catalog-viewport-${width}.png` });
      const footer = page.locator(".site-footer");
      const alignment = await footer.evaluate(node => {
        const links = [...node.querySelectorAll(".footer-links > a")].map(link => link.getBoundingClientRect());
        const left = Math.min(...links.map(r => r.left)), right = Math.max(...links.map(r => r.right));
        const bounds = node.getBoundingClientRect();
        return { text: getComputedStyle(node).textAlign, nav: getComputedStyle(node.querySelector("nav")).justifyContent,
          center: Math.abs((left + right) / 2 - (bounds.left + bounds.right) / 2), touch: links.every(r => r.height >= 44),
          icons: node.querySelectorAll(".footer-links > a > svg").length };
      });
      assert.equal(alignment.text, "center");
      assert.equal(alignment.nav, "center");
      assert.ok(alignment.center < 2 && alignment.touch);
      assert.equal(alignment.icons, 2);
      await footer.screenshot({ path: `.qa/screenshots/footer-${width}.png` });
      await page.evaluate(() => scrollTo(0, 0));
    }
    await accessible();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator("#catalog-search").fill("QA Marca");
    await page.getByRole("button", { name: "Buscar", exact: true }).click();
    await page.waitForURL(url => url.searchParams.get("q") === "QA Marca");
    await page.locator(".category-select button").waitFor({ state: "hidden" });
    assert.equal(await page.locator(".product-card").count(), 1);
    await page.locator("#category-filter").selectOption("qa-cotillon");
    await page.waitForURL(url => url.searchParams.get("categoria") === "qa-cotillon");
    await page.getByRole("heading", { name: "No encontramos productos" }).waitFor();
    assert.equal(await page.locator("#catalog-search").inputValue(), "QA Marca");
    assert.equal(await page.locator("#category-filter").inputValue(), "qa-cotillon");
    assert.equal(new URL(page.url()).searchParams.get("categoria"), "qa-cotillon");
    assert.equal(await page.getByRole("button", { name: "Filtrar", exact: true }).isVisible(), false);
    const instagram = page.getByRole("link", { name: /Instagram/ });
    assert.equal(await instagram.getAttribute("target"), "_blank");
    assert.equal(await instagram.getAttribute("rel"), "noopener noreferrer");
    await page.goto(base);
  });

  await t.test("imagen ampliada reutiliza foto, cierra con teclado/fondo y restaura foco", async () => {
    const photos = page.locator(".product-image-open");
    const trigger = photos.first();
    assert.equal(await photos.count(), 3);
    for (const width of [360, 390, 430, 768, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      const ratios = [];
      for (const photo of await photos.all()) {
        await photo.scrollIntoViewIfNeeded();
        const dimensions = await photo.locator("img").evaluate(async img => {
          await img.decode();
          const frame = img.closest(".product-image").getBoundingClientRect();
          const link = img.parentElement.getBoundingClientRect(), box = img.getBoundingClientRect();
          const scale = Math.max(box.width / img.naturalWidth, box.height / img.naturalHeight);
          const paintedWidth = img.naturalWidth * scale, paintedHeight = img.naturalHeight * scale;
          return { height: frame.height, linkHeight: link.height, imageHeight: box.height,
            fits: box.left >= frame.left && box.right <= frame.right && box.top >= frame.top && box.bottom <= frame.bottom,
            ratio: img.naturalWidth / img.naturalHeight, fit: getComputedStyle(img).objectFit,
            centered: getComputedStyle(img).objectPosition === "50% 50%",
            paintedWidth, paintedHeight, width: frame.width };
        });
        assert.ok(Math.abs(dimensions.height - dimensions.width) < .1);
        assert.equal(dimensions.linkHeight, dimensions.height);
        assert.equal(dimensions.imageHeight, dimensions.height);
        assert.equal(dimensions.fits && dimensions.centered, true);
        assert.equal(dimensions.fit, "cover");
        assert.ok(dimensions.paintedWidth >= dimensions.width - .1 && dimensions.paintedHeight >= dimensions.height - .1);
        ratios.push(dimensions.ratio);
        await photo.screenshot({ path: `.qa/screenshots/photo-${width}-${ratios.length}.png` });
        await photo.click();
        const preview = page.locator("#product-image-dialog");
        await preview.waitFor();
        const expanded = await preview.locator("img").evaluate(async img => {
          await img.decode();
          const r = img.getBoundingClientRect();
          return { ratio: img.naturalWidth / img.naturalHeight, fit: getComputedStyle(img).objectFit,
            inside: r.left >= 0 && r.right <= innerWidth && r.top >= 0 && r.bottom <= innerHeight };
        });
        assert.equal(expanded.ratio, dimensions.ratio);
        assert.equal(expanded.fit, "contain");
        assert.equal(expanded.inside, true);
        await preview.screenshot({ path: `.qa/screenshots/expanded-${width}-${ratios.length}.png` });
        await page.keyboard.press("Escape");
        await preview.waitFor({ state: "hidden" });
        assert.equal(await photo.evaluate(node => node === document.activeElement), true);
      }
      assert.deepEqual(ratios, [1.5, 1, 0.5]);
      const frames = await page.locator(".product-image").evaluateAll(nodes => nodes.map(node => {
        const r = node.getBoundingClientRect(); return { width: r.width, height: r.height };
      }));
      assert.ok(frames.every(frame => Math.abs(frame.width - frame.height) < .1 && Math.abs(frame.width - frames[0].width) < .1));
    }
    assert.equal(await page.locator(".product-card").filter({ has: page.locator(".image-placeholder") }).locator(".product-image-open").count(), 0);
    await trigger.focus();
    await trigger.press("Enter");
    const dialog = page.locator("#product-image-dialog");
    await dialog.waitFor();
    assert.equal(await dialog.locator("h1, h2, h3, .product-brand, .product-description").count(), 0);
    assert.equal(await dialog.evaluate(node => [...node.children].filter(child => !child.classList.contains("visually-hidden")).map(child => child.innerText.trim()).filter(Boolean).join(" ")), "×");
    assert.equal(await dialog.getAttribute("aria-label"), "Imagen ampliada");
    assert.equal(await dialog.getByRole("button", { name: "Cerrar imagen" }).count(), 1);
    assert.equal(await dialog.locator("img").getAttribute("src"), await trigger.locator("img").evaluate(node => node.src));
    for (const width of [360, 390, 430, 768, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      assert.equal(await dialog.locator("img").evaluate(node => getComputedStyle(node).objectFit), "contain");
      await page.screenshot({ path: `.qa/screenshots/image-${width}.png` });
    }
    await accessible();
    await page.screenshot({ path: ".qa/screenshots/image-expanded.png" });
    for (const height of [300, 390]) {
      await page.setViewportSize({ width: 844, height });
      const fitting = await dialog.evaluate(node => {
        const frame = node.getBoundingClientRect(), image = node.querySelector("img").getBoundingClientRect();
        return { scroll: node.scrollHeight > node.clientHeight, inside: image.top >= frame.top && image.bottom <= frame.bottom };
      });
      assert.equal(fitting.scroll, false);
      assert.equal(fitting.inside, true);
      await page.screenshot({ path: `.qa/screenshots/image-landscape-${height}.png` });
    }
    await page.keyboard.press("Escape");
    await dialog.waitFor({ state: "hidden" });
    await page.waitForFunction(() => document.activeElement?.classList.contains("product-image-open"));
    await trigger.click();
    await page.locator("#image-dialog-close").click();
    await dialog.waitFor({ state: "hidden" });
    await trigger.click();
    await page.mouse.click(1, 1);
    await dialog.waitFor({ state: "hidden" });
    assert.equal(await trigger.evaluate(node => node === document.activeElement), true);
    const plain = await browser.newContext({ javaScriptEnabled: false });
    const plainPage = await plain.newPage();
    await plainPage.goto(base);
    const imageUrl = await plainPage.locator(".product-image-open").first().getAttribute("href");
    const imageRequest = plainPage.waitForRequest(request => new URL(request.url()).pathname === imageUrl && request.isNavigationRequest());
    await plainPage.locator(".product-image-open").first().click();
    assert.equal(new URL((await imageRequest).url()).pathname, imageUrl);
    await plain.close();
    await page.setViewportSize({ width: 390, height: 844 });
  });

  await t.test("Instagram oficial abre otro contexto seguro y conserva catálogo", async () => {
    await context.route("https://www.instagram.com/_dulceysalado1/", route => route.fulfill({ contentType: "text/html", body: "<h1>Instagram interceptado de QA</h1>" }));
    const original = page.url();
    const opening = context.waitForEvent("page");
    await page.getByRole("link", { name: /Instagram/ }).click();
    const instagram = await opening;
    await instagram.getByRole("heading", { name: "Instagram interceptado de QA" }).waitFor();
    assert.equal(instagram.url(), "https://www.instagram.com/_dulceysalado1/");
    assert.equal(await instagram.evaluate(() => window.opener), null);
    assert.equal(await instagram.evaluate(() => document.referrer), "");
    assert.equal(page.url(), original);
    await instagram.close();
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
    await card.locator(".quantity-error").filter({ hasText: /múltiplo/ }).waitFor();
    await card.locator('input[name="quantity"]').fill("0.10");
  });

  await t.test("notificaciones flotantes con scroll, temporizador, pausa, reemplazo y cierre", async () => {
    const isolated = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const client = await isolated.newPage();
    try {
      await client.clock.install();
      await client.goto(base);
      const card = client.locator(".product-card").nth(8);
      const add = card.getByRole("button", { name: "Agregar al carrito" });
      await add.scrollIntoViewIfNeeded();
      await add.focus();
      const before = await client.evaluate(() => scrollY);
      assert.ok(before > 2000);
      await add.click();
      const toast = client.locator("[data-notification]:visible");
      await toast.waitFor();
      assert.equal(await toast.count(), 1);
      assert.ok(Math.abs(await client.evaluate(() => scrollY) - before) < 3);
      assert.equal(await add.evaluate(node => node === document.activeElement), true);
      assert.equal(await client.locator(".product-feedback").count(), 0);
      for (const width of [360, 390, 430, 768, 1280]) {
        await client.setViewportSize({ width, height: 844 });
        const bounds = await toast.boundingBox();
        assert.ok(bounds.y >= 16 && bounds.y + bounds.height <= 844);
        assert.ok(bounds.x >= 16 && bounds.x + bounds.width <= width - 16);
      }
      await client.setViewportSize({ width: 390, height: 844 });
      await client.screenshot({ path: ".qa/screenshots/floating-success.png" });
      await toast.getByRole("link", { name: "Ver carrito" }).focus();
      await client.mouse.move(0, 800);
      await client.clock.fastForward(10000);
      assert.equal(await toast.isVisible(), true);
      await client.locator(".skip-link").focus();
      await client.clock.fastForward(5100);
      assert.equal(await toast.count(), 0);
      await client.evaluate(() => Notifications.show("Información breve", "info"));
      await client.clock.fastForward(4000);
      await client.evaluate(() => Notifications.show("Advertencia nueva", "warning"));
      await client.clock.fastForward(4000);
      assert.equal(await toast.locator("[data-notification-message]").innerText(), "Advertencia nueva");
      await toast.getByRole("button", { name: "Cerrar notificación" }).press("Enter");
      assert.equal(await toast.count(), 0);
      await client.evaluate(() => Notifications.show("Error puntual", "error"));
      await client.mouse.move(0, 800);
      await client.clock.fastForward(7900);
      assert.equal(await toast.isVisible(), true);
      await client.clock.fastForward(200);
      assert.equal(await toast.count(), 0);

      const first = client.locator(".product-card").first();
      await first.getByRole("button", { name: "Agregar al carrito" }).click();
      await first.locator('select[name="price_type"]').selectOption("wholesale");
      await first.getByRole("button", { name: "Agregar al carrito" }).click();
      await toast.getByRole("alert").filter({ hasText: /otra selección/ }).waitFor();
      assert.equal(await client.locator('[role="alert"]:visible').count(), 1);
      assert.ok((await toast.boundingBox()).y >= 16);
      await accessible(client);
      await client.screenshot({ path: ".qa/screenshots/floating-error.png" });
      await first.locator('input[name="quantity"]').fill("0.15");
      await first.getByRole("button", { name: "Agregar al carrito" }).click();
      await first.locator(".quantity-error").waitFor();
      assert.equal(await first.locator('input[name="quantity"]').getAttribute("aria-invalid"), "true");
      await client.mouse.move(0, 800);
      await client.clock.fastForward(8100);
      assert.equal(await first.locator(".quantity-error").isVisible(), true);
      assert.equal(await toast.count(), 0);
      await client.goto(`${base}/carrito/`);
      await client.locator(".total").waitFor();
      await client.locator(".cart-quantity").first().fill("0.15");
      await client.locator(".cart-quantity").first().dispatchEvent("change");
      await client.locator("[data-cart-error]").filter({ hasText: /múltiplo/ }).waitFor();
      await client.mouse.move(0, 800);
      await client.clock.fastForward(8100);
      assert.equal(await client.locator("[data-cart-error]").filter({ hasText: /múltiplo/ }).isVisible(), true);
      assert.equal(await client.locator("#cart-review").isDisabled(), true);
      assert.equal(await client.locator(".total").count(), 0);
      assert.equal(await client.locator("[data-notification]:visible").count(), 0);
    } finally { await isolated.close(); }
  });

  await t.test("cantidad, mayorista manual y persistencia al cerrar pestaña", async () => {
    const card = page.locator(".product-card").filter({ hasText: "QA Chocolate (test)" });
    await card.locator('input[name="quantity"]').fill("0.3");
    await card.locator('select[name="price_type"]').selectOption("wholesale");
    await card.getByRole("button", { name: "Agregar al carrito" }).click();
    await page.getByRole("status").filter({ hasText: "Producto agregado" }).waitFor();
    assert.equal(await page.getByRole("link", { name: "Ver carrito" }).isVisible(), true);
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
    assert.equal(await page.locator(".cart-item .wholesale-note").count(), 1);
    assert.equal(await page.locator("#cart-clear, .cart-toolbar").count(), 0);
    assert.equal(await page.locator("#cart-reset").isVisible(), false);
    for (const width of [320, 360, 390, 430, 640, 768, 800, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const thumbnail = page.locator(".cart-thumbnail").first();
      assert.equal((await thumbnail.boundingBox()).width, width >= 800 ? 132 : 56);
      if (width >= 800) {
        const aligned = await page.locator(".cart-item").first().evaluate(node => {
          const photo = node.querySelector(".cart-thumbnail").getBoundingClientRect();
          const fields = node.querySelectorAll("h2, .product-brand, [data-cart-amount], .wholesale-note, .product-controls, [data-cart-error]");
          return Array.from(fields).filter(field => field.getBoundingClientRect().height > 0)
            .every(field => field.getBoundingClientRect().left >= photo.right + 12);
        });
        assert.equal(aligned, true);
      }
      const remove = page.getByRole("button", { name: "Quitar QA Chocolate (test) del carrito", exact: true });
      const bounds = await remove.boundingBox();
      assert.ok(bounds.width >= 44 && bounds.height >= 44);
      assert.equal(await remove.innerText(), "");
      assert.equal(await remove.locator('svg[aria-hidden="true"][focusable="false"]').count(), 1);
      assert.equal(await thumbnail.locator("img").evaluate(node => getComputedStyle(node).objectFit), "contain");
      await thumbnail.click();
      assert.equal(await page.locator("#product-image-expanded").getAttribute("src"), await thumbnail.locator("img").evaluate(node => node.src));
      await page.keyboard.press("Escape");
      assert.equal(await thumbnail.evaluate(node => node === document.activeElement), true);
      await page.screenshot({ path: `.qa/screenshots/cart-${width}.png`, fullPage: true });
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await accessible();
    await page.getByRole("button", { name: /Aumentar cantidad/ }).click();
    await waitCart("$ 36,20");
    await page.getByRole("button", { name: /Reducir cantidad/ }).click();
    await waitCart("$ 27,15");
    await page.screenshot({ path: ".qa/screenshots/cart-mobile.png", fullPage: true });
    await setQuantity("0.5");
    await waitCart("$ 45,25");
    await page.locator(".cart-thumbnail").click();
    await page.getByRole("button", { name: "Cerrar imagen" }).click();
    assert.equal(await page.locator(".cart-thumbnail").evaluate(node => node === document.activeElement), true);
    await setQuantity("0.15");
    await page.locator("[data-cart-error]").filter({ hasText: /La cantidad debe ser positiva/ }).waitFor();
    assert.equal(await page.locator("#cart-review").isDisabled(), true);
    await setQuantity("0.3");
    await waitCart("$ 27,15");
  });

  await t.test("papelera con teclado quita sólo el artículo elegido y conserva los restantes", async () => {
    const isolated = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const client = await isolated.newPage();
    try {
      await client.goto(base);
      await client.locator(".add-product").first().waitFor();
      const items = await client.locator(".add-product").evaluateAll(forms => {
        const items = forms.slice(0, 2).map(form => ({ id: Number(form.dataset.id), quantity: form.elements.quantity.value,
          price_type: "retail", sale_unit: form.dataset.unit, revision: form.dataset.revision }));
        localStorage.setItem("dulce-salado.cart.v1", JSON.stringify({ version: 1, items }));
        return items;
      });
      await client.goto(`${base}/carrito/`);
      await client.locator(".total").waitFor();
      assert.equal(await client.locator(".cart-item").count(), 2);
      const chosen = client.locator(`.cart-item[data-id="${items[1].id}"]`);
      const name = await chosen.locator("h2").innerText();
      const remove = chosen.getByRole("button", { name: `Quitar ${name} del carrito`, exact: true });
      await remove.focus();
      await remove.press("Enter");
      await chosen.waitFor({ state: "detached" });
      assert.equal(await client.locator(".cart-item").count(), 1);
      assert.equal(await client.locator(".cart-item").getAttribute("data-id"), String(items[0].id));
      const stored = JSON.parse(await client.evaluate(() => localStorage.getItem("dulce-salado.cart.v1"))).items;
      assert.equal(stored.length, 1);
      assert.equal(stored[0].id, items[0].id);
      assert.equal(stored[0].quantity, items[0].quantity);
      assert.equal(await client.locator("[data-cart-count]").innerText(), "1");
      await client.locator("[data-notification]:visible").waitFor();
      await accessible(client);
    } finally { await isolated.close(); }
  });

  await t.test("Admin descarga CSV y variantes PDF del conjunto filtrado", async () => {
    await admin.goto(`${base}/admin/catalog/product/?q=Scroll&sale_unit__exact=unidad&is_active__exact=1`);
    const downloaded = admin.waitForEvent("download");
    await admin.getByRole("link", { name: "Exportar CSV", exact: true }).click();
    const download = await downloaded;
    const bytes = readFileSync(await download.path());
    assert.equal(bytes.subarray(0, 3).equals(Buffer.from([0xef, 0xbb, 0xbf])), true);
    const lines = bytes.toString("utf8").trim().split(/\r?\n/);
    assert.equal(lines.length, 11);
    assert.equal(lines.slice(1).every(line => line.includes("ZZZ QA Scroll") && line.endsWith(";Sí")), true);
    for (const [label, variant] of [["PDF con imágenes", "con-imagenes"], ["PDF sin imágenes", "sin-imagenes"],
                                  ["PDF tabla compacta", "tabla-compacta"], ["PDF tabla con imágenes", "tabla-con-imagenes"]]) {
      const link = admin.getByRole("link", { name: label, exact: true });
      const url = new URL(await link.getAttribute("href"), base);
      assert.equal(url.searchParams.get("q"), "Scroll");
      assert.equal(url.searchParams.get("sale_unit__exact"), "unidad");
      assert.equal(url.searchParams.get("is_active__exact"), "1");
      const pending = admin.waitForEvent("download");
      await link.click();
      const pdf = await pending;
      assert.equal(pdf.suggestedFilename(), `dulce-y-salado-productos-${variant}.pdf`);
      assert.equal(readFileSync(await pdf.path()).subarray(0, 5).toString(), "%PDF-");
    }
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
      await scrolled.locator("#cart-request-error").filter({ hasText: /Los importes no se muestran/ }).waitFor();
      assert.equal(await input.isVisible(), true);
      assert.equal(await input.evaluate(node => node === window.qaQuantityNode), true);
      assert.equal(await scrolled.locator(".total").isVisible(), false);
      assert.equal(await scrolled.locator("#cart-review").isDisabled(), true);
      await scrolled.unrouteAll({ behavior: "wait" });
      await scrolled.getByRole("button", { name: "Reintentar" }).click();
      await scrolled.locator(".total").filter({ hasText: "$ 50,13" }).waitFor();
      await scrolled.setViewportSize({ width: 1280, height: 844 });
      await input.evaluate(node => { node.scrollIntoView({ block: "center" }); node.focus({ preventScroll: true }); });
      const desktopScroll = await scrolled.evaluate(() => scrollY);
      assert.ok(desktopScroll > 1000);
      let desktopArrived, desktopRelease;
      const desktopRequested = new Promise(resolve => { desktopArrived = resolve; });
      const desktopGate = new Promise(resolve => { desktopRelease = resolve; });
      await scrolled.route("**/carrito/recalcular/", async route => { desktopArrived(); await desktopGate; await route.continue(); });
      try {
        await input.fill("7"); await input.dispatchEvent("change"); await desktopRequested;
        assert.equal(await input.evaluate(node => node === window.qaQuantityNode && node === document.activeElement), true);
        assert.ok(Math.abs(await scrolled.evaluate(() => scrollY) - desktopScroll) < 3);
        desktopRelease();
        await scrolled.locator(".total").filter({ hasText: "$ 51,13" }).waitFor();
        assert.equal(await input.evaluate(node => node === window.qaQuantityNode && node === document.activeElement), true);
        assert.ok(Math.abs(await scrolled.evaluate(() => scrollY) - desktopScroll) < 3);
        await scrolled.screenshot({ path: ".qa/screenshots/cart-desktop-scroll.png" });
      } finally { desktopRelease(); await scrolled.unrouteAll({ behavior: "wait" }); }
    } finally { unblock(); await isolated.close(); }
  });

  await t.test("mayorista retirado exige selección explícita", async () => {
    await editPrices("100.25", "");
    await page.reload();
    await page.locator("[data-cart-error]").filter({ hasText: /El precio mayorista ya no está disponible/ }).waitFor();
    assert.equal(await page.locator("#cart-review").isDisabled(), true);
    await page.locator(".cart-price").selectOption("retail");
    await waitCart("$ 30,08");
    assert.equal(await page.locator(".cart-item .wholesale-note").count(), 0);
  });

  await t.test("diálogo accesible, Escape cancela, cambio posterior exige nueva revisión", async () => {
    await page.locator("#cart-review").click();
    await page.getByRole("dialog").waitFor();
    assert.equal(await page.locator("#review-title").evaluate(node => node === document.activeElement), true);
    await accessible();
    await page.screenshot({ path: ".qa/screenshots/review-mobile.png", fullPage: true });
    await page.evaluate(() => { navigator.clipboard.writeText = async text => { window.qaCopied = text; }; });
    await page.locator("#copy-message").click();
    await page.getByRole("dialog").getByRole("status").filter({ hasText: "Mensaje copiado." }).waitFor();
    assert.equal(await page.evaluate(() => window.qaCopied), await page.locator("#whatsapp-message").inputValue());
    assert.equal(await page.locator("#copy-message").innerText(), "Copiar mensaje completo");
    await page.evaluate(() => { navigator.clipboard.writeText = async () => { throw new Error("QA clipboard blocked"); }; });
    await page.locator("#copy-message").click();
    await page.getByRole("dialog").getByRole("status").filter({ hasText: /Copiá el texto seleccionado/ }).waitFor();
    assert.equal(await page.locator("#whatsapp-message").evaluate(node => node === document.activeElement && node.selectionStart === 0 && node.selectionEnd === node.value.length), true);
    await accessible();
    const afterClose = page.waitForResponse(response => response.url().endsWith("/carrito/recalcular/"));
    await page.keyboard.press("Escape");
    await page.getByRole("dialog").waitFor({ state: "hidden" });
    await afterClose;
    await page.waitForFunction(() => document.activeElement?.id === "cart-review" && !document.getElementById("cart-review")?.disabled);
    assert.equal(await page.evaluate(() => document.activeElement?.id), "cart-review");
    await page.locator("#cart-review").click();
    await page.getByRole("dialog").waitFor();
    await editPrices("200.50", "90.50");
    const changedPopup = page.waitForEvent("popup");
    await page.locator("#review-continue").click();
    const provisional = await changedPopup;
    await page.locator("[data-review-notice]").filter({ hasText: /cambió la información/ }).waitFor();
    if (!provisional.isClosed()) await provisional.waitForEvent("close");
    assert.equal(provisional.isClosed(), true);
    assert.equal(page.url(), `${base}/carrito/`);
    assert.match(await page.locator("#whatsapp-message").inputValue(), /Total estimado: \$ 60,15/);
  });

  await t.test("WhatsApp interceptado incluye mensaje completo; no envía ni borra carrito", async () => {
    let destination;
    await context.route(/^https:\/\/wa\.me\//, async route => {
      destination = route.request().url();
      await route.fulfill({ contentType: "text/html; charset=utf-8", body: "<h1>Salida interceptada de QA</h1>" });
    });
    const opening = page.waitForEvent("popup");
    await page.locator("#review-continue").click();
    const whatsapp = await opening;
    await whatsapp.getByRole("heading", { name: "Salida interceptada de QA" }).waitFor();
    assert.equal(page.url(), `${base}/carrito/`);
    assert.equal(await whatsapp.evaluate(() => window.opener), null);
    assert.equal(await whatsapp.evaluate(() => document.referrer), "");
    const url = new URL(destination);
    assert.equal(url.pathname, "/5491100000000");
    assert.match(url.searchParams.get("text"), /precio minorista \$ 200,50\/kg/);
    assert.match(url.searchParams.get("text"), /cantidad 0,3 kg/);
    assert.match(url.searchParams.get("text"), /Total estimado: \$ 60,15/);
    const stored = JSON.parse(await page.evaluate(() => localStorage.getItem("dulce-salado.cart.v1")));
    assert.equal(stored.items.length, 1);
    await whatsapp.close();
    await page.goto(`${base}/carrito/`);
    await waitCart("$ 60,15");
  });

  await t.test("bloqueo de popup conserva enlace validado seguro y apertura manual", async () => {
    await page.evaluate(() => { window.qaNativeOpen = window.open; window.open = () => null; });
    try {
      await page.locator("#cart-review").click();
      await page.getByRole("dialog").waitFor();
      const before = context.pages().length;
      await page.locator("#review-continue").click();
      const ready = page.locator("#whatsapp-ready");
      await ready.waitFor();
      assert.equal(context.pages().length, before);
      assert.equal(await ready.getAttribute("target"), "_blank");
      assert.equal(await ready.getAttribute("rel"), "noopener noreferrer");
      assert.equal(await page.locator("#review-continue").isVisible(), false);
      await accessible();
      const opening = context.waitForEvent("page");
      await ready.click();
      const whatsapp = await opening;
      await whatsapp.getByRole("heading", { name: "Salida interceptada de QA" }).waitFor();
      assert.equal(await whatsapp.evaluate(() => window.opener), null);
      assert.equal(await whatsapp.evaluate(() => document.referrer), "");
      assert.equal(page.url(), `${base}/carrito/`);
      await whatsapp.close();
      await page.locator("#review-cancel").click();
      await waitCart("$ 60,15");
    } finally { await page.evaluate(() => { window.open = window.qaNativeOpen; }); }
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
    const opening = page.waitForEvent("popup");
    await page.locator("#review-continue").click();
    const provisional = await opening;
    await reached;
    const closed = provisional.waitForEvent("close");
    await page.locator("#review-cancel").click();
    await closed;
    await waitCart("$ 60,15");
    assert.equal(provisional.isClosed(), true);
    const cancelledResponse = page.waitForResponse(response => response.url().endsWith("/carrito/whatsapp/"));
    release();
    await cancelledResponse;
    await page.unroute("**/carrito/whatsapp/");
    assert.equal(page.url(), `${base}/carrito/`);
    assert.equal(await page.getByRole("dialog").isVisible(), false);
  });

  await t.test("error al preparar WhatsApp cierra pestaña provisional y conserva carrito", async () => {
    await page.route("**/carrito/whatsapp/", route => route.abort());
    try {
      await page.locator("#cart-review").click();
      await page.getByRole("dialog").waitFor();
      const opening = page.waitForEvent("popup");
      await page.locator("#review-continue").click();
      const provisional = await opening;
      if (!provisional.isClosed()) await provisional.waitForEvent("close");
      await page.getByRole("alert").filter({ hasText: /fetch|verificar/ }).waitFor();
      assert.equal(page.url(), `${base}/carrito/`);
      await waitCart("$ 60,15");
      assert.equal(JSON.parse(await page.evaluate(() => localStorage.getItem("dulce-salado.cart.v1"))).items.length, 1);
    } finally { await page.unroute("**/carrito/whatsapp/"); }
  });

  await t.test("cambio en otra pestaña durante validación cancela salida pendiente", async () => {
    const second = await context.newPage();
    await second.goto(base);
    let release, reached;
    const gate = new Promise(resolve => { release = resolve; });
    const arrived = new Promise(resolve => { reached = resolve; });
    const destinations = [];
    const track = request => { if (request.url().startsWith("https://wa.me/")) destinations.push(request.url()); };
    context.on("request", track);
    await page.route("**/carrito/whatsapp/", async route => { reached(); await gate; await route.continue(); });
    try {
      await page.locator("#cart-review").click();
      await page.getByRole("dialog").waitFor();
      const opening = page.waitForEvent("popup");
      await page.locator("#review-continue").click();
      const provisional = await opening;
      await arrived;
      const closed = provisional.waitForEvent("close");
      await second.evaluate(() => {
        const cart = JSON.parse(localStorage.getItem("dulce-salado.cart.v1"));
        cart.items[0].quantity = "0.4";
        localStorage.setItem("dulce-salado.cart.v1", JSON.stringify(cart));
      });
      await closed;
      await waitCart("$ 80,20");
      const response = page.waitForResponse(response => response.url().endsWith("/carrito/whatsapp/"));
      release(); await response;
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      assert.deepEqual(destinations, []);
      assert.equal(await page.getByRole("dialog").isVisible(), false);
      assert.equal(page.url(), `${base}/carrito/`);
      await second.evaluate(() => {
        const cart = JSON.parse(localStorage.getItem("dulce-salado.cart.v1"));
        cart.items[0].quantity = "0.3";
        localStorage.setItem("dulce-salado.cart.v1", JSON.stringify(cart));
      });
      await waitCart("$ 60,15");
    } finally { release(); await page.unrouteAll({ behavior: "wait" }); context.off("request", track); await second.close(); }
  });

  await t.test("cambio de unidad exige cantidad nueva y sincroniza pestañas", async () => {
    await admin.goto(`${base}/admin/catalog/product/${chocolateId}/change/`);
    await admin.locator("#id_sale_unit").selectOption("unidad");
    await admin.locator("#id_quantity_step").fill("1");
    await admin.locator('input[name="_save"]').click();
    await page.reload();
    await page.locator("[data-cart-error]").filter({ hasText: /Cambió la unidad de venta/ }).waitFor();
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
    await page.locator("#cart-request-error").filter({ hasText: /Los importes no se muestran/ }).waitFor();
    assert.equal(await page.locator(".total").count(), 0);
    await page.unroute("**/carrito/recalcular/");
    await page.getByRole("button", { name: "Reintentar" }).click();
    await waitCart("$ 601,50");
    await admin.goto(`${base}/admin/catalog/product/${chocolateId}/change/`);
    await admin.locator("#id_is_active").uncheck();
    await admin.locator('input[name="_save"]').click();
    await page.reload();
    await page.locator("[data-cart-error]").filter({ hasText: /Este producto ya no está disponible/ }).waitFor();
    assert.equal(await page.locator("#cart-review").isDisabled(), true);
    await page.getByRole("button", { name: /Quitar producto/ }).click();
    await page.getByRole("heading", { name: "Tu carrito está vacío" }).waitFor();
  });

  await t.test("almacenamiento corrupto recuperable y sin errores JS", async () => {
    await page.evaluate(() => { localStorage.setItem("dulce-salado.cart.v1", "invalid"); localStorage.setItem("qa-other-data", "preservar"); });
    await page.reload();
    await page.locator("#cart-storage-error").filter({ hasText: /El carrito guardado no se pudo leer/ }).waitFor();
    assert.equal(await page.evaluate(() => localStorage.getItem("dulce-salado.cart.v1")), "invalid");
    await page.getByRole("button", { name: "Restablecer carrito" }).click();
    await page.getByRole("heading", { name: "Tu carrito está vacío" }).waitFor();
    assert.equal(await page.evaluate(() => localStorage.getItem("qa-other-data")), "preservar");
    assert.equal(await page.locator("#cart-reset").isVisible(), false);
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
    await blockedPage.locator("#cart-storage-error").filter({ hasText: /No se pudo guardar el carrito/ }).waitFor();
    await blockedPage.goto(`${base}/carrito/`);
    await blockedPage.getByRole("heading", { name: "Tu carrito está vacío" }).waitFor();
    assert.equal(await blockedPage.locator("#cart-review").count(), 0);
    await blocked.close();
    const unreadable = await browser.newContext();
    await unreadable.addInitScript(() => {
      Storage.prototype.getItem = function () { throw new DOMException("Test storage blocked", "SecurityError"); };
    });
    const unreadablePage = await unreadable.newPage();
    unreadablePage.on("pageerror", error => errors.push(error.message));
    await unreadablePage.goto(`${base}/carrito/`);
    await unreadablePage.locator("#cart-storage-error").filter({ hasText: /Habilitá el almacenamiento local/ }).waitFor();
    assert.equal(await unreadablePage.locator("#cart-reset").isVisible(), false);
    assert.equal(await unreadablePage.locator("#cart-review").count(), 0);
    await unreadable.close();
  });

  await t.test("Ubicación sin dirección y configuración única desde Admin", async () => {
    await page.locator(".header-actions").getByRole("link", { name: "Ubicación", exact: true }).click();
    assert.equal(await page.locator('.header-actions a[aria-current="page"]').getAttribute("href"), "/ubicacion/");
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
    const iframe = page.locator(".location-map iframe");
    assert.equal(await page.getByRole("heading", { name: "Cómo llegar", exact: true }).count(), 0);
    assert.equal(await page.getByRole("heading", { name: "Ubicación", level: 1 }).count(), 1);
    assert.equal(await page.locator(".business-card .business-address address").count(), 1);
    assert.equal(await page.locator(".business-card .location-map iframe").count(), 1);
    await page.frameLocator(".location-map iframe").getByRole("button", { name: "Interactuar con mapa de QA" }).click();
    await page.frameLocator(".location-map iframe").getByRole("button", { name: "Mapa interactuado" }).waitFor();
    assert.equal(await iframe.getAttribute("title"), "Ubicación de Dulce y Salado en Google Maps");
    assert.equal(await iframe.getAttribute("loading"), "lazy");
    assert.equal(await iframe.getAttribute("referrerpolicy"), "strict-origin-when-cross-origin");
    assert.equal(await iframe.getAttribute("allowfullscreen"), "");
    assert.match(await iframe.getAttribute("src"), /^https:\/\/www\.google\.com\/maps\/embed\?pb=!1m18/);
    for (const width of [360, 390, 430, 768, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const map = await iframe.boundingBox();
      const info = await page.locator(".business-address").boundingBox();
      assert.equal(await page.locator(".business-address").evaluate(node => getComputedStyle(node).textAlign), "center");
      const region = await page.locator(".business-card").boundingBox();
      assert.ok(map.x >= region.x && map.x + map.width <= region.x + region.width);
      if (width >= 800) {
        assert.ok(info.x + info.width <= map.x && info.y >= map.y && info.y + info.height <= map.y + map.height);
      } else {
        assert.ok(info.y + info.height <= map.y && Math.abs(info.x - map.x) < 2);
      }
      assert.ok(map.width <= width - 32 && map.height >= 280 && map.height <= 460);
      await page.screenshot({ path: `.qa/screenshots/directions-${width}.png`, fullPage: true });
      await accessible();
    }
    await accessible();
    await page.route(/^https:\/\/www\.google\.com\/maps\//, route => route.fulfill({ contentType: "text/html", body: "<h1>Mapa interceptado de QA</h1>" }));
    await maps.click();
    await page.getByRole("heading", { name: "Mapa interceptado de QA" }).waitFor();
    await page.goto(`${base}/ubicacion/`);
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
    assert.equal(await page.locator("header .hours-panel").count(), 1);
    assert.equal(await page.locator(".weekly-hours > div").count(), 7);
    const separators = await page.locator(".weekly-hours > div").evaluateAll(nodes => nodes.map(node => getComputedStyle(node).borderTopWidth));
    assert.deepEqual(separators, ["0px", "1px", "1px", "1px", "1px", "1px", "1px"]);
    assert.match(await page.locator(".weekly-hours dd").first().innerText(), /09:00–12:00\s+15:00–18:00/);
    assert.equal(await page.locator(".weekly-hours dd").nth(1).innerText(), "Cerrado");
    for (const width of [360, 390, 430, 768, 800, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const layout = await page.evaluate(() => {
        const panel = document.querySelector(".hours-panel"), header = document.querySelector("header");
        const before = document.querySelector("main").getBoundingClientRect().top;
        panel.open = false;
        const after = document.querySelector("main").getBoundingClientRect().top;
        panel.open = true;
        const bounds = document.querySelector(".hours-details").getBoundingClientRect();
        return { before, after, height: header.getBoundingClientRect().height, left: bounds.left, right: bounds.right };
      });
      assert.equal(layout.before, layout.after);
      assert.ok(layout.height < (width >= 800 ? 120 : 200));
      await headerLayout(width);
      assert.ok(layout.left >= 0 && layout.right <= width);
      await page.screenshot({ path: `.qa/screenshots/hours-${width}.png`, fullPage: true });
      await accessible();
    }
    await accessible();
    await page.locator(".hours-panel summary").press("Enter");
    assert.equal(await page.locator(".hours-panel").evaluate(node => node.open), false);
    await page.locator(".hours-panel summary").press("Enter");
    await page.keyboard.press("Escape");
    assert.equal(await page.locator(".hours-panel").evaluate(node => node.open), false);
    assert.equal(await page.locator(".hours-panel summary").evaluate(node => node === document.activeElement), true);
    await page.locator(".hours-panel summary").click();
    await page.locator(".site-footer p").first().click();
    assert.equal(await page.locator(".hours-panel").evaluate(node => node.open), false);
    await page.locator(".hours-panel summary").click();
    await page.frameLocator(".location-map iframe").getByRole("heading", { name: "Mapa interceptado de QA" }).click();
    await page.waitForFunction(() => !document.querySelector(".hours-panel").open);
    assert.equal(await page.evaluate(() => document.activeElement.tagName), "IFRAME");
    const plain = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 360, height: 844 } });
    const plainPage = await plain.newPage();
    await plain.route("https://www.google.com/maps/embed?*", route => route.abort());
    await plainPage.goto(`${base}/ubicacion/`);
    await plainPage.locator(".hours-panel summary").click();
    assert.equal(await plainPage.locator(".weekly-hours").isVisible(), true);
    await plain.close();
    assert.deepEqual(errors, []);
  });

  await t.test("carrito con nombre largo, foto vigente y ausencia de foto sin espacio extra", async () => {
    await page.goto(`${base}/?q=QA%20Velas`);
    const id = await page.locator(".add-product").getAttribute("data-id");
    const name = "QA Velas decorativas para cumpleaños con colores surtidos y presentación de prueba ".repeat(2).trim();
    await admin.goto(`${base}/admin/catalog/product/${id}/change/`);
    await admin.locator("#id_name").fill(name);
    await admin.locator('input[name="_save"]').click();
    await admin.locator(".messagelist .success").waitFor();
    await page.reload();
    await page.getByRole("button", { name: "Agregar al carrito" }).click();
    await page.goto(`${base}/carrito/`);
    await waitCart("$ 25,10");
    for (const width of [320, 360, 390, 430, 768, 800, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      const layout = await page.locator(".cart-item-heading").evaluate(node => {
        const name = node.querySelector("h2").getBoundingClientRect();
        const remove = node.querySelector("button").getBoundingClientRect();
        const photo = node.querySelector(".cart-thumbnail").getBoundingClientRect();
        return { separated: photo.right <= name.left && name.right <= remove.left, fits: document.documentElement.scrollWidth <= innerWidth };
      });
      assert.ok(layout.separated && layout.fits);
      await page.locator(".cart-thumbnail").click();
      await page.keyboard.press("Escape");
      await page.screenshot({ path: `.qa/screenshots/cart-long-name-${width}.png`, fullPage: true });
      await accessible();
    }
    await page.getByRole("button", { name: /Aumentar cantidad/ }).click();
    await waitCart("$ 50,20");
    await page.locator(".cart-thumbnail").click();
    await page.getByRole("button", { name: "Cerrar imagen" }).click();
    assert.equal(await page.locator(".cart-thumbnail").evaluate(node => node === document.activeElement), true);
    assert.equal(await page.evaluate(() => /image|media|\.webp/.test(localStorage.getItem("dulce-salado.cart.v1"))), false);
    await admin.goto(`${base}/admin/catalog/product/${id}/change/`);
    await admin.locator('input[name="image-clear"]').check();
    await admin.locator('input[name="_save"]').click();
    await admin.locator(".messagelist .success").waitFor();
    await page.reload();
    await waitCart("$ 50,20");
    assert.equal(await page.locator(".cart-thumbnail, .cart-item .image-placeholder").count(), 0);
    for (const width of [320, 390, 800, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      const aligned = await page.locator(".cart-item").evaluate(node => {
        const left = node.getBoundingClientRect().left;
        const heading = node.querySelector("h2").getBoundingClientRect().left;
        const controls = node.querySelector(".product-controls").getBoundingClientRect().left;
        return Math.abs(heading - controls) < 1 && heading - left < 24 && document.documentElement.scrollWidth <= innerWidth;
      });
      assert.equal(aligned, true);
      await page.screenshot({ path: `.qa/screenshots/cart-no-photo-${width}.png`, fullPage: true });
    }
    await page.getByRole("button", { name: /Quitar QA Velas/ }).click();
    await page.getByRole("heading", { name: "Tu carrito está vacío" }).waitFor();
    assert.deepEqual(errors, []);
  });

  await t.test("45 fixtures demo: cuatro páginas, filtros y GET sin JavaScript", async () => {
    // Altas explícitas sólo en la base descartable del servidor QA, mediante Admin.
    // No ejecuta seed_demo_catalog automáticamente como fixture de navegador.
    const groups = JSON.parse(readFileSync("catalog/management/demo_products.json", "utf8"));
    await admin.goto(`${base}/admin/catalog/category/add/`);
    const token = await admin.locator('#category_form input[name="csrfmiddlewaretoken"]').inputValue();
    const slugs = {};
    for (const category of Object.keys(groups)) {
      const slug = category.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
      slugs[category] = slug;
      const result = await context.request.post(`${base}/admin/catalog/category/add/`, {
        form: { csrfmiddlewaretoken: token, name: category, slug, sort_order: "0", is_active: "on", _save: "Guardar" },
      });
      assert.equal(result.url(), `${base}/admin/catalog/category/`);
    }
    await admin.goto(`${base}/admin/catalog/product/add/`);
    for (const [category, rows] of Object.entries(groups)) {
      const [id] = await admin.locator("#id_category").selectOption({ label: category });
      for (const [name, unit, step, retail, wholesale, condition] of rows) {
        const result = await context.request.post(`${base}/admin/catalog/product/add/`, {
          form: { csrfmiddlewaretoken: token, category: id, name: `[DEMO] ${name}`, brand: `Marca Demo ${category}`,
            description: "Producto ficticio para pruebas aisladas.", sale_unit: unit, quantity_step: step,
            retail_price: retail, wholesale_price: wholesale || "", wholesale_condition: condition, is_active: "on", _save: "Guardar" },
        });
        assert.equal(result.url(), `${base}/admin/catalog/product/`);
      }
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${base}/?q=${encodeURIComponent("[DEMO]")}`);
    const seen = [];
    for (const [number, start, end] of [[1, 1, 12], [2, 13, 24], [3, 25, 36], [4, 37, 45]]) {
      await page.getByText(`${start}–${end} de 45 productos`, { exact: false }).waitFor();
      assert.equal(await page.locator(".product-card").count(), end - start + 1);
      await page.getByText(`Página ${number} de 4`, { exact: true }).waitFor();
      seen.push(...await page.locator(".product-card").evaluateAll(nodes => nodes.map(node => node.getAttribute("aria-labelledby"))));
      if (number < 4) {
        await page.getByRole("link", { name: "Siguiente", exact: true }).click();
        await page.waitForURL(url => url.searchParams.get("page") === String(number + 1));
        assert.equal(new URL(page.url()).searchParams.get("q"), "[DEMO]");
      }
    }
    assert.equal(new Set(seen).size, 45);
    assert.equal(await page.getByRole("link", { name: "Siguiente", exact: true }).count(), 0);
    await page.getByRole("link", { name: "Anterior", exact: true }).click();
    await page.waitForURL(url => url.searchParams.get("page") === "3");
    for (const width of [360, 390, 430, 768, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      await page.goto(`${base}/?q=${encodeURIComponent("[DEMO]")}`);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const targets = await page.locator(".pagination a").evaluateAll(nodes => nodes.map(node => node.getBoundingClientRect().height));
      assert.ok(targets.every(height => height >= 44));
      await page.screenshot({ path: `.qa/screenshots/demo-catalog-${width}.png`, fullPage: true });
      await page.locator(".pagination").screenshot({ path: `.qa/screenshots/demo-pagination-${width}.png` });
      await accessible();
    }
    await page.setViewportSize({ width: 390, height: 844 });
    for (const slug of Object.values(slugs)) {
      await page.goto(`${base}/?q=${encodeURIComponent("[DEMO]")}&categoria=${slug}`);
      await page.getByText("1–12 de 15 productos", { exact: false }).waitFor();
      await page.getByRole("link", { name: "Siguiente", exact: true }).click();
      await page.waitForURL(url => url.searchParams.get("page") === "2");
      assert.equal(new URL(page.url()).searchParams.get("categoria"), slug);
      assert.equal(new URL(page.url()).searchParams.get("q"), "[DEMO]");
      assert.equal(await page.locator(".product-card").count(), 3);
      await page.getByText("13–15 de 15 productos", { exact: false }).waitFor();
    }
    const plain = await browser.newContext({ javaScriptEnabled: false });
    const plainPage = await plain.newPage();
    await plainPage.goto(`${base}/?q=${encodeURIComponent("[DEMO]")}&categoria=reposteria`);
    await plainPage.getByRole("link", { name: "Siguiente", exact: true }).click();
    await plainPage.getByText("13–15 de 15 productos", { exact: false }).waitFor();
    assert.equal(new URL(plainPage.url()).searchParams.get("q"), "[DEMO]");
    await plain.close();
    assert.deepEqual(errors, []);
  });
});
