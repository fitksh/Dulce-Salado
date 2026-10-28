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
  async function selectMobileCategory(target, name) {
    await target.locator(".mobile-categories summary").click();
    await target.locator(".category-menu").getByRole("link", { name, exact: true }).click();
  }
  async function headerLayout(width) {
    if (width < 768) {
      const boxes = await page.locator(".header-inner").evaluate(node => [".brand", ".search-form", ".cart-link", ".header-info"].map(selector => node.querySelector(selector).getBoundingClientRect().toJSON()));
      assert.ok(boxes.every(box => box.left >= 8 && box.right <= width - 8));
      assert.ok(boxes.slice(0, 3).every(box => Math.abs(box.top + box.height / 2 - boxes[0].top - boxes[0].height / 2) < 1));
      assert.ok(boxes[0].right <= boxes[1].left && boxes[1].right <= boxes[2].left);
      assert.ok(boxes[3].top >= boxes[0].bottom);
      return;
    }
    const regions = await page.locator(".header-inner").evaluate(node => [".brand", ".search-form", ".header-actions"].map(selector => {
      const r = node.querySelector(selector).getBoundingClientRect();
      return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2 };
    }));
    assert.ok(regions.every(r => r.left >= 16 && r.right <= width - 16));
    if (width >= 1050) {
      assert.ok(regions.every(r => Math.abs(r.y - regions[0].y) < 2));
      assert.ok(regions[0].right <= regions[1].left && regions[1].right <= regions[2].left);
    } else if (width >= 600) {
      assert.ok(Math.abs(regions[0].y - regions[2].y) < 2);
      assert.ok(regions[0].right <= regions[2].left && regions[2].bottom <= regions[1].top);
    } else {
      assert.ok(regions[0].bottom <= regions[1].top && regions[1].bottom <= regions[2].top);
    }
  }

  async function setQuantity(value) {
    const input = page.locator(".cart-quantity").first();
    if (/^[0-9]+$/.test(value)) await input.fill(value);
    else await input.evaluate((node, value) => { node.value = value; node.dispatchEvent(new Event("change", { bubbles: true })); }, value);
    await input.press("Tab");
  }
  async function photosCentered(target) {
    const offsets = await target.locator(".cart-item:has(.cart-thumbnail)").evaluateAll(rows => rows.map(row => {
      const card = row.getBoundingClientRect(), photo = row.querySelector(".cart-thumbnail").getBoundingClientRect();
      return Math.abs(card.top + card.height / 2 - photo.top - photo.height / 2);
    }));
    assert.ok(offsets.length && offsets.every(offset => offset < 1), JSON.stringify(offsets));
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
    assert.equal(await page.locator(".wholesale-note, .prices dt").count(), 0);
    assert.equal(await page.getByText("Minorista", { exact: true }).count(), 0);
    assert.equal(await page.getByText("Mayorista", { exact: true }).count(), 0);
    assert.equal(await page.getByText("QA Invisible").count(), 0);
    for (const [width, columns] of [[320, 2], [360, 2], [375, 2], [390, 2], [430, 2], [767, 2], [768, 2], [800, 3], [1000, 3], [1280, 4], [1440, 5]]) {
      await page.setViewportSize({ width, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const cards = await page.locator(".product-card").evaluateAll(nodes => nodes.map(node => {
        const r = node.getBoundingClientRect();
        return { top: r.top, titleTop: node.querySelector("h3").getBoundingClientRect().top, descriptionTop: node.querySelector(".product-description")?.getBoundingClientRect().top, priceTop: node.querySelector(".product-price").getBoundingClientRect().top, height: r.height, controlBottom: node.querySelector(".catalog-stepper").getBoundingClientRect().bottom, width: r.width, fits: [...node.querySelectorAll("input, select, button")].every(control => {
          const c = control.getBoundingClientRect(); return c.height === 0 || (c.left >= r.left && c.right <= r.right);
        }) };
      }));
      assert.equal(cards.filter(card => Math.abs(card.top - cards[0].top) < 1).length, columns);
      assert.ok(cards.every(card => Math.abs(card.width - cards[0].width) < 1 && card.fits));
      for (const card of cards) {
        const row = cards.filter(other => Math.abs(other.top - card.top) < 1);
        assert.ok(row.every(other => Math.abs(other.titleTop - card.titleTop) < 1), `Títulos desalineados a ${width}px`);
        assert.ok(row.every(other => Math.abs(other.priceTop - card.priceTop) < 1), `Precios desalineados a ${width}px`);
        if (card.descriptionTop !== undefined) assert.ok(row.filter(other => other.descriptionTop !== undefined).every(other => Math.abs(other.descriptionTop - card.descriptionTop) < 1), `Descripciones desalineadas a ${width}px`);
        assert.ok(row.every(other => Math.abs(other.height - card.height) < 1), `Alturas distintas en fila a ${width}px`);
        assert.ok(row.every(other => Math.abs(other.controlBottom - card.controlBottom) < 1), `Controles desalineados a ${width}px`);
      }
      const cartLink = page.locator(".header-actions .cart-link");
      assert.ok((await cartLink.getAttribute("href")).endsWith("/carrito/"));
      assert.equal(await cartLink.evaluate(node => {
        const copy = node.cloneNode(true);
        copy.querySelectorAll(".visually-hidden, svg").forEach(hidden => hidden.remove());
        return copy.textContent.trim();
      }), "0");
      assert.equal(await page.getByRole("link", { name: "Carrito: 0 productos diferentes" }).count(), 1);
      await headerLayout(width);
      assert.equal(await page.locator(".brand-logo").evaluate(node => node.getBoundingClientRect().width), width < 768 ? 40 : 64);
      const actions = await page.locator(width < 768 ? ".header-info .header-control, .hours-unavailable" : ".header-actions > a, .header-control, .hours-unavailable").evaluateAll(nodes => nodes.map(node => node.getBoundingClientRect().toJSON()).filter(box => box.height));
      assert.equal(actions.length, 3);
      assert.ok(actions.every(action => Math.abs(action.top + action.height / 2 - actions[0].top - actions[0].height / 2) < 1));
      assert.equal(await page.locator('.header-actions > a[aria-current="page"]').count(), 0);
      assert.equal(await page.locator(".catalog-bar").getByRole("link", { name: "Catálogo", exact: true }).count(), 0);
      const targets = await page.locator("button, input:not([type=hidden]), select, .button, .chip").evaluateAll(nodes => nodes.filter(n => n.getBoundingClientRect().height > 0).map(n => ({ tag: n.tagName, height: n.getBoundingClientRect().height, search: !!n.closest(".search-form") })));
      assert.equal(targets.every(target => target.height >= (width < 768 && target.search ? 36 : 44)), true, JSON.stringify(targets));
      const steppers = await page.locator(".quantity-adjust").evaluateAll(nodes => nodes.map(n => n.getBoundingClientRect().width));
      assert.equal(steppers.every(width => width >= 44), true);
      await page.screenshot({ path: `.qa/screenshots/catalog-${width}.png`, fullPage: true });
      await page.screenshot({ path: `.qa/screenshots/catalog-viewport-${width}.png` });
      const footer = page.locator(".site-footer");
      const alignment = await footer.evaluate(node => {
        const links = [...node.querySelectorAll(".footer-links > *")].map(link => link.getBoundingClientRect());
        const left = Math.min(...links.map(r => r.left)), right = Math.max(...links.map(r => r.right));
        const bounds = node.getBoundingClientRect();
        return { text: getComputedStyle(node).textAlign, nav: getComputedStyle(node.querySelector("nav")).justifyContent,
          center: Math.abs((left + right) / 2 - (bounds.left + bounds.right) / 2), touch: links.every(r => r.height >= 44),
          icons: node.querySelectorAll(".footer-links > * > svg").length };
      });
      assert.equal(alignment.text, "center");
      assert.equal(alignment.nav, "center");
      assert.ok(alignment.center < 2 && alignment.touch);
      assert.equal(alignment.icons, 2);
      await footer.screenshot({ path: `.qa/screenshots/footer-${width}.png` });
      await page.evaluate(() => scrollTo(0, 0));
    }
    // Sólo esta página descartable: contenido permitido por el modelo, sin escribir datos.
    await page.locator(".product-card").first().evaluate(card => {
      card.querySelector("h3").textContent = "N".repeat(180);
      card.querySelector(".product-description").textContent = "Descripción extensa. ".repeat(20);
    });
    for (const width of [390, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      const card = page.locator(".product-card").first();
      assert.ok(await card.evaluate(node => [...node.querySelectorAll("h3, p, input, select, button")].every(field => field.scrollWidth <= field.clientWidth + 1)));
      await card.screenshot({ path: `.qa/screenshots/catalog-long-text-${width}.png` });
    }
    await page.reload();
    await accessible();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator("#catalog-search").fill("QA Marca");
    await page.getByRole("button", { name: "Buscar", exact: true }).click();
    await page.waitForURL(url => url.searchParams.get("q") === "QA Marca");
    await page.locator(".category-select button").waitFor({ state: "hidden" });
    assert.equal(await page.locator(".product-card").count(), 1);
    await selectMobileCategory(page, "QA Cotillón (test)");
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

  await t.test("buscador y categorías del header navegan desde carrito y conservan filtros", async () => {
    await page.goto(`${base}/carrito/`);
    await page.locator("header #catalog-search").fill("QA Marca");
    await page.getByRole("button", { name: "Buscar", exact: true }).click();
    await page.waitForURL(url => url.pathname === "/" && url.searchParams.get("q") === "QA Marca");
    assert.equal(await page.locator(".product-card").count(), 1);
    await page.setViewportSize({ width: 1280, height: 844 });
    await page.locator(".categories").getByRole("link", { name: "QA Cotillón (test)", exact: true }).click();
    await page.getByRole("heading", { name: "No encontramos productos" }).waitFor();
    assert.equal(new URL(page.url()).searchParams.get("q"), "QA Marca");
    assert.equal(new URL(page.url()).searchParams.get("categoria"), "qa-cotillon");
    await page.locator(".categories").getByRole("link", { name: "Todas las categorías", exact: true }).click();
    assert.equal(await page.locator(".product-card").count(), 1);
    assert.equal(await page.locator("#catalog-search").inputValue(), "QA Marca");
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${base}/carrito/`);
    await selectMobileCategory(page, "QA Cotillón (test)");
    await page.waitForURL(url => url.pathname === "/" && url.searchParams.get("categoria") === "qa-cotillon");
    assert.equal(await page.locator(".product-card").count(), 1);
    assert.equal(await page.locator("#catalog-search").inputValue(), "");
    const plain = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
    const plainPage = await plain.newPage();
    await plainPage.goto(`${base}/carrito/`);
    await selectMobileCategory(plainPage, "QA Cotillón (test)");
    await plainPage.waitForURL(url => url.pathname === "/" && url.searchParams.get("categoria") === "qa-cotillon");
    assert.equal(await plainPage.locator(".product-card").count(), 1);
    await plain.close();
    await page.goto(base);
  });

  await t.test("imagen ampliada reutiliza foto, cierra con teclado/fondo y restaura foco", async () => {
    const photos = page.locator(".product-image-open");
    const trigger = photos.first();
    assert.equal(await photos.count(), 3);
    for (const [width, height] of [[360, 800], [390, 844], [430, 932], [768, 844], [844, 300], [1280, 800], [1440, 900]]) {
      await page.setViewportSize({ width, height });
      const ratios = [];
      for (const photo of await photos.all()) {
        await photo.scrollIntoViewIfNeeded();
        const dimensions = await photo.locator("img").evaluate(async img => {
          await img.decode();
          const frame = img.closest(".product-image").getBoundingClientRect();
          const link = img.parentElement.getBoundingClientRect(), box = img.getBoundingClientRect();
          const scale = (innerWidth < 768 ? Math.min : Math.max)(box.width / img.naturalWidth, box.height / img.naturalHeight);
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
        assert.equal(dimensions.fit, width < 768 ? "contain" : "cover");
        if (width < 768) assert.ok(dimensions.paintedWidth <= dimensions.width + .1 && dimensions.paintedHeight <= dimensions.height + .1);
        else assert.ok(dimensions.paintedWidth >= dimensions.width - .1 && dimensions.paintedHeight >= dimensions.height - .1);
        ratios.push(dimensions.ratio);
        await photo.screenshot({ path: `.qa/screenshots/photo-${width}-${ratios.length}.png` });
        await photo.click();
        const preview = page.locator("#product-image-dialog");
        await preview.waitFor();
        const expanded = await preview.locator("img").evaluate(async img => {
          await img.decode();
          const r = img.getBoundingClientRect();
          const frame = img.closest("dialog"), box = frame.getBoundingClientRect();
          return { ratio: img.naturalWidth / img.naturalHeight, fit: getComputedStyle(img).objectFit,
            renderedRatio: r.width / r.height,
            unscaled: r.width <= img.naturalWidth + .1 && r.height <= img.naturalHeight + .1,
            margins: [r.left - box.left, box.right - r.right, r.top - box.top, box.bottom - r.bottom],
            scroll: frame.scrollHeight > frame.clientHeight || frame.scrollWidth > frame.clientWidth,
            inside: r.left >= 0 && r.right <= innerWidth && r.top >= 0 && r.bottom <= innerHeight };
        });
        assert.equal(expanded.ratio, dimensions.ratio);
        assert.equal(expanded.fit, "contain");
        assert.equal(expanded.inside, true);
        assert.ok(Math.abs(expanded.renderedRatio - expanded.ratio) < .001);
        assert.equal(expanded.unscaled, true);
        assert.ok(expanded.margins.slice(0, 2).every(gap => gap >= 23));
        assert.ok(expanded.margins[2] >= 63 && expanded.margins[3] >= 23);
        assert.equal(await preview.evaluate(node => getComputedStyle(node).backgroundColor), "rgba(0, 0, 0, 0)");
        assert.equal(expanded.scroll, false);
        const close = await preview.getByRole("button", { name: "Cerrar imagen" }).boundingBox();
        assert.ok(close.width >= 44 && close.height >= 44);
        await page.screenshot({ path: `.qa/screenshots/viewer-${width}x${height}-${ratios.length}.png` });
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
    assert.equal(await dialog.evaluate(node => [...node.children].filter(child => !child.classList.contains("visually-hidden")).map(child => child.innerText.trim()).filter(Boolean).join(" ")), "");
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

  await t.test("categorías sin JavaScript y estados más, basura y menos con teclado", async () => {
    const plain = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 360, height: 844 } });
    const plainPage = await plain.newPage();
    await plainPage.goto(`${base}/?q=QA`);
    await selectMobileCategory(plainPage, "QA Cotillón (test)");
    assert.equal(await plainPage.locator(".product-card").count(), 1);
    assert.equal(await plainPage.locator("#catalog-search").inputValue(), "QA");
    assert.equal(await plainPage.locator("#category-filter").inputValue(), "qa-cotillon");
    await plain.close();
    const card = page.locator(".product-card").first();
    assert.equal(await card.locator(".product-category, .product-brand, select, input:not(.catalog-amount)").count(), 0);
    assert.equal(await card.locator(".catalog-decrease").isVisible(), false);
    assert.equal(await card.locator(".catalog-amount").isVisible(), false);
    await card.locator(".catalog-increase").press("Enter");
    assert.equal(await card.locator(".catalog-amount").inputValue(), "1");
    assert.equal(await card.locator(".catalog-trash").isVisible(), true);
    assert.equal(await card.locator(".catalog-minus").isVisible(), false);
    await card.locator(".catalog-increase").press("Enter");
    assert.equal(await card.locator(".catalog-amount").inputValue(), "2");
    assert.equal(await card.locator(".catalog-minus").isVisible(), true);
    assert.equal(await card.locator(".catalog-trash").isVisible(), false);
    await card.locator(".catalog-decrease").click();
    assert.equal(await card.locator(".catalog-trash").isVisible(), true);
    assert.equal(await card.locator(".catalog-minus").isVisible(), false);
    await card.locator(".catalog-decrease").press("Enter");
    assert.equal(await card.locator(".catalog-decrease").isVisible(), false);
    assert.equal(await card.locator(".catalog-increase").evaluate(node => node === document.activeElement), true);
    await page.getByRole("status").filter({ hasText: "Producto eliminado" }).waitFor();
  });

  await t.test("notificaciones flotantes con scroll, temporizador, pausa, reemplazo y cierre", async () => {
    const isolated = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const client = await isolated.newPage();
    try {
      await client.clock.install();
      await client.goto(base);
      const card = client.locator(".product-card").nth(8);
      const add = card.locator(".catalog-increase");
      await add.scrollIntoViewIfNeeded();
      await add.focus();
      const before = await client.evaluate(() => scrollY);
      assert.ok(before > 1000);
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
        assert.ok(bounds.x >= 15 && bounds.x + bounds.width <= width - 15);
        assert.ok(Math.abs(bounds.x + bounds.width / 2 - width / 2) < 1);
        assert.ok(Math.abs(bounds.y - 16) < 1);
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
      await first.locator(".catalog-increase").click();
      await client.evaluate(() => {
        const saved = JSON.parse(localStorage.getItem("dulce-salado.cart.v1"));
        saved.items[0].quantity = "0.3";
        localStorage.setItem("dulce-salado.cart.v1", JSON.stringify(saved));
      });
      // El clic relee storage y conserva la fracción para corregirla explícitamente.
      await card.locator(".catalog-increase").click();
      await toast.getByRole("alert").filter({ hasText: /entera|múltiplo/ }).waitFor();
      assert.equal(await card.locator(".catalog-error").isVisible(), false);
      assert.equal(await card.locator(".catalog-trash").isVisible(), false);
      assert.equal(await card.locator(".catalog-minus").isVisible(), true);
      await accessible(client);
      await client.screenshot({ path: ".qa/screenshots/floating-error.png" });
      await client.mouse.move(0, 800);
      await client.clock.fastForward(8100);
      assert.equal(await card.locator(".catalog-error").isVisible(), false);
      assert.equal(await toast.count(), 0);
      await client.evaluate(() => {
        const saved = JSON.parse(localStorage.getItem("dulce-salado.cart.v1"));
        saved.items[0].quantity = "1";
        localStorage.setItem("dulce-salado.cart.v1", JSON.stringify(saved));
      });
      await client.goto(`${base}/carrito/`);
      await client.locator(".total").waitFor();
      await client.locator(".cart-quantity").first().evaluate(node => { node.value = "0.15"; });
      await client.locator(".cart-quantity").first().dispatchEvent("change");
      await client.getByRole("alert").filter({ hasText: /enteras, sin decimales/ }).waitFor();
      await client.mouse.move(0, 800);
      await client.clock.fastForward(8100);
      assert.equal(await client.locator("[data-cart-error]:not([hidden])").count(), 0);
      assert.equal(await client.locator(".cart-quantity").first().getAttribute("aria-invalid"), "true");
      assert.equal(await client.locator("#cart-review").isDisabled(), true);
      assert.equal(await client.locator(".total").count(), 0);
      assert.equal(await client.locator("[data-notification]:visible").count(), 0);
    } finally { await isolated.close(); }
  });

  await t.test("cantidad, precio publicado y persistencia al cerrar pestaña", async () => {
    const card = page.locator(".product-card").filter({ hasText: "QA Chocolate (test)" });
    await card.locator(".catalog-increase").click({ clickCount: 1 });
    await card.locator(".catalog-increase").click();
    await card.locator(".catalog-increase").click();
    await page.getByRole("status").filter({ hasText: "Se agregó QA Chocolate (test) al carrito." }).waitFor();
    assert.equal(await page.getByRole("link", { name: "Ver carrito" }).isVisible(), true);
    assert.equal(await page.locator("[data-cart-count]").innerText(), "1");
    await accessible();
    await page.goto(`${base}/carrito/`);
    await waitCart("$ 300");
    const stored = JSON.parse(await page.evaluate(() => localStorage.getItem("dulce-salado.cart.v1")));
    assert.equal(stored.items[0].quantity, "3.00");
    assert.equal(stored.items[0].price_type, "retail");
    assert.equal("price" in stored.items[0], false);
    await page.close();
    page = await context.newPage();
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(`${base}/carrito/`);
    await waitCart("$ 300");
    assert.equal(await page.locator(".cart-price, .product-brand, .wholesale-note").count(), 0);
    assert.equal(await page.getByText("Minorista", { exact: true }).count(), 0);
    assert.equal(await page.getByText("Tipo de precio", { exact: true }).count(), 0);
    assert.equal(await page.locator("#cart-clear, .cart-toolbar").count(), 0);
    assert.equal(await page.locator("#cart-reset").isVisible(), false);
    for (const width of [320, 360, 390, 430, 640, 768, 800, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const thumbnail = page.locator(".cart-thumbnail").first();
      assert.equal((await thumbnail.boundingBox()).width, width >= 800 ? 132 : 56);
      if (width >= 800) {
        await photosCentered(page);
        const aligned = await page.locator(".cart-item").first().evaluate(node => {
          const photo = node.querySelector(".cart-thumbnail").getBoundingClientRect();
          const fields = node.querySelectorAll("h2, .product-brand, [data-cart-amount], .wholesale-note, .product-controls, [data-cart-error]");
          return Array.from(fields).filter(field => field.getBoundingClientRect().height > 0)
            .every(field => field.getBoundingClientRect().left >= photo.right + 12);
        });
        assert.equal(aligned, true);
      }
      const decrease = page.getByRole("button", { name: "Reducir cantidad de QA Chocolate (test)", exact: true });
      const bounds = await decrease.boundingBox();
      assert.ok(bounds.width >= 44 && bounds.height >= 44);
      assert.equal(await decrease.locator(".cart-minus").isVisible(), true);
      assert.equal(await decrease.locator(".trash-icon").isVisible(), false);
      const alignedRight = await page.locator(".cart-item").first().evaluate(row => {
        const bounds = row.getBoundingClientRect(), plus = row.querySelector('[data-direction="1"]').getBoundingClientRect();
        return Math.abs(bounds.right - parseFloat(getComputedStyle(row).paddingRight) - 1 - plus.right) < 1;
      });
      assert.equal(alignedRight, true);
      assert.equal(await thumbnail.locator("img").evaluate(node => getComputedStyle(node).objectFit), "contain");
      await thumbnail.click();
      assert.equal(await page.locator("#product-image-expanded").getAttribute("src"), await thumbnail.locator("img").evaluate(node => node.src));
      await page.keyboard.press("Escape");
      assert.equal(await thumbnail.evaluate(node => node === document.activeElement), true);
      await page.screenshot({ path: `.qa/screenshots/cart-${width}.png`, fullPage: true });
    }
    await photosCentered(page);
    const desktopQuantity = page.locator(".cart-quantity");
    await desktopQuantity.focus();
    const desktopScroll = await page.evaluate(() => scrollY);
    await desktopQuantity.fill("4");
    await desktopQuantity.dispatchEvent("change");
    await waitCart("$ 400");
    assert.equal(await desktopQuantity.evaluate(node => node === document.activeElement), true);
    assert.ok(Math.abs(await page.evaluate(() => scrollY) - desktopScroll) < 3);
    await photosCentered(page);
    const desktopIncrease = page.getByRole("button", { name: /Aumentar cantidad/ });
    await desktopIncrease.focus();
    const buttonScroll = await page.evaluate(() => scrollY);
    await desktopIncrease.press("Enter");
    await waitCart("$ 500");
    assert.equal(await desktopIncrease.evaluate(node => node === document.activeElement), true);
    assert.ok(Math.abs(await page.evaluate(() => scrollY) - buttonScroll) < 3);
    await photosCentered(page);
    await setQuantity("3");
    await waitCart("$ 300");
    await photosCentered(page);
    await page.setViewportSize({ width: 390, height: 844 });
    await accessible();
    await page.getByRole("button", { name: /Aumentar cantidad/ }).click();
    await waitCart("$ 400");
    await page.getByRole("button", { name: /Reducir cantidad/ }).click();
    await waitCart("$ 300");
    await page.screenshot({ path: ".qa/screenshots/cart-mobile.png", fullPage: true });
    await setQuantity("5");
    await waitCart("$ 500");
    await page.locator(".cart-thumbnail").click();
    await page.getByRole("button", { name: "Cerrar imagen" }).click();
    assert.equal(await page.locator(".cart-thumbnail").evaluate(node => node === document.activeElement), true);
    await setQuantity("0.15");
    await page.getByRole("alert").filter({ hasText: /enteras, sin decimales/ }).waitFor();
    assert.equal(await page.locator("[data-cart-error]:not([hidden])").count(), 0);
    assert.equal(await page.locator("#cart-review").isDisabled(), true);
    await setQuantity("3");
    await waitCart("$ 300");
  });

  await t.test("papelera con teclado quita sólo el artículo elegido y conserva los restantes", async () => {
    const isolated = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const client = await isolated.newPage();
    try {
      await client.goto(base);
      await client.locator(".add-product").first().waitFor();
      const items = await client.locator(".add-product").evaluateAll(forms => {
        const items = forms.slice(0, 2).map(form => ({ id: Number(form.dataset.id), quantity: "1",
          price_type: "retail", sale_unit: form.dataset.unit, revision: form.dataset.revision }));
        localStorage.setItem("dulce-salado.cart.v1", JSON.stringify({ version: 1, items }));
        return items;
      });
      await client.evaluate(() => {
        const saved = JSON.parse(localStorage.getItem("dulce-salado.cart.v1"));
        saved.items[0].quantity = "1";
        localStorage.setItem("dulce-salado.cart.v1", JSON.stringify(saved));
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
      assert.equal(await client.locator("[data-notification]:visible").count(), 0);
      await accessible(client);
    } finally { await isolated.close(); }
  });

  await t.test("Admin descarga CSV y variantes PDF del conjunto filtrado", async () => {
    await admin.goto(`${base}/admin/catalog/product/?q=Scroll&sale_unit__exact=kg&is_active__exact=1`);
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
      assert.equal(url.searchParams.get("sale_unit__exact"), "kg");
      assert.equal(url.searchParams.get("is_active__exact"), "1");
      const pending = admin.waitForEvent("download");
      await link.click();
      const pdf = await pending;
      assert.equal(pdf.suggestedFilename(), `dulce-y-salado-productos-${variant}.pdf`);
      assert.equal(readFileSync(await pdf.path()).subarray(0, 5).toString(), "%PDF-");
    }
  });

  await t.test("Admin importa sólo después de vista previa y confirmación, omite duplicados y muestra errores", async () => {
    await admin.goto(`${base}/admin/catalog/product/`);
    await admin.getByRole("link", { name: "Importar CSV", exact: true }).click();
    const pending = admin.waitForEvent("download");
    await admin.getByRole("link", { name: "Descargar plantilla CSV", exact: true }).click();
    const template = await pending;
    assert.equal(template.suggestedFilename(), "dulce-y-salado-plantilla-productos.csv");
    assert.ok(readFileSync(await template.path()).toString("utf8").includes("CATEGORÍA EXISTENTE;[EJEMPLO]"));
    const headers = "Categoría;Nombre;Marca;Descripción;Unidad de venta;Incremento de cantidad;Precio minorista;Precio mayorista;Condición mayorista;Activo\n";
    const quoted = fields => fields.map(value => `"${value.replaceAll('"', '""')}"`).join(";");
    const bad = headers + quoted(["QA Repostería (test)", '<img src=x onerror="alert(1)">', "", "", "kg", "", "1", "", "", "No"]);
    await admin.locator("#id_csv_file").setInputFiles({ name: "invalid.csv", mimeType: "text/csv", buffer: Buffer.from(bad) });
    assert.equal(await admin.getByRole("heading", { name: "Vista previa" }).count(), 0);
    await admin.getByRole("button", { name: "Analizar archivo", exact: true }).click();
    await admin.getByRole("heading", { name: "Vista previa" }).waitFor();
    await admin.waitForLoadState("load");
    assert.equal(await admin.getByRole("button", { name: "Confirmar importación", exact: true }).count(), 0);
    assert.equal(await admin.locator("#result_list img").count(), 0);
    assert.equal(await admin.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await accessible(admin);
    await admin.screenshot({ path: ".qa/screenshots/csv-import-error-390.png", fullPage: true });
    const content = headers + [
      ["QA Repostería (test)", "QA Importado (test)", "", 'QA ñ; "comillas"\nsegunda línea', "kg", "1", "14500", "", "", "No"],
      ["QA Repostería (test)", "QA Chocolate (test)", "QA Marca", "Producto descartable de prueba; no representa información comercial.", "kg", "", "9999", "", "", "Sí"],
    ].map(quoted).join("\n");
    await admin.locator("#id_csv_file").setInputFiles({ name: "productos.csv", mimeType: "text/csv", buffer: Buffer.from(content) });
    await admin.getByRole("button", { name: "Analizar archivo", exact: true }).click();
    await admin.getByRole("button", { name: "Confirmar importación", exact: true }).waitFor();
    await admin.waitForLoadState("load");
    assert.ok((await admin.locator("#content").innerText()).includes("1 nuevos · 1 duplicados · 0 filas con errores"));
    assert.equal(await admin.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    const region = admin.getByRole("region", { name: "Vista previa de productos" });
    await region.focus();
    await region.press("ArrowRight");
    await admin.waitForTimeout(150);
    assert.ok(await region.evaluate(node => node.scrollLeft > 0));
    await region.evaluate(node => { node.scrollLeft = 0; });
    await accessible(admin);
    await admin.screenshot({ path: ".qa/screenshots/csv-import-preview-390.png", fullPage: true });
    const check = await context.newPage();
    await check.goto(`${base}/admin/catalog/product/?q=QA+Importado`);
    assert.equal(await check.locator("#result_list tbody tr").count(), 0);
    await check.close();
    await admin.setViewportSize({ width: 1280, height: 844 });
    await admin.screenshot({ path: ".qa/screenshots/csv-import-preview-1280.png", fullPage: true });
    await admin.getByRole("button", { name: "Confirmar importación", exact: true }).click();
    await admin.getByText("Importación completada:", { exact: false }).waitFor();
    assert.ok((await admin.locator(".messagelist").innerText()).includes("1 productos creados y 1 duplicados omitidos"));
    assert.equal(await admin.getByRole("heading", { name: "Vista previa" }).count(), 0);
    await admin.goto(`${base}/admin/catalog/product/?q=QA+Importado`);
    assert.equal(await admin.locator("#result_list tbody tr").count(), 1);
    await admin.locator("#result_list tbody tr th a").click();
    assert.equal(await admin.locator("#id_quantity_step").count(), 0);
    assert.equal(await admin.locator("#id_retail_price").inputValue(), "14500");
    assert.equal(await admin.locator("#id_is_active").isChecked(), false);
    await admin.setViewportSize({ width: 390, height: 844 });
  });

  await t.test("carrito largo conserva control, foco y scroll durante y después del recálculo", async () => {
    const isolated = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const scrolled = await isolated.newPage();
    await scrolled.goto(base);
    await scrolled.locator(".add-product").first().waitFor();
    await scrolled.locator(".add-product").evaluateAll(forms => {
      const items = forms.map(form => ({ id: Number(form.dataset.id), quantity: "1",
        price_type: "retail", sale_unit: form.dataset.unit, revision: form.dataset.revision }));
      localStorage.setItem("dulce-salado.cart.v1", JSON.stringify({ version: 1, items }));
    });
    await scrolled.goto(`${base}/carrito/`);
    await scrolled.locator(".total").waitFor();
    const input = scrolled.locator(".cart-quantity").nth(8);
    await input.evaluate(node => { node.scrollIntoView({ block: "center" }); node.focus({ preventScroll: true }); window.qaQuantityNode = node; });
    const before = await scrolled.evaluate(() => scrollY);
    assert.ok(before > 1000);
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
      assert.match(await scrolled.locator(".total").innerText(), /136/);
      await scrolled.unrouteAll({ behavior: "wait" });
      const increase = scrolled.locator(".cart-item").nth(8).locator('[data-direction="1"]');
      await increase.evaluate(node => { node.focus({ preventScroll: true }); window.qaIncreaseNode = node; });
      await increase.press("Enter");
      await scrolled.locator(".total").filter({ hasText: "$ 137" }).waitFor();
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
        await scrolled.locator(".total").filter({ hasText: "$ 139" }).waitFor();
        const stale = scrolled.waitForResponse(response => response.url().endsWith("/carrito/recalcular/"));
        pending[0].send(); await stale;
        await scrolled.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        assert.match(await scrolled.locator(".total").innerText(), /139/);
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
      await scrolled.locator(".total").filter({ hasText: "$ 140" }).waitFor();
      await scrolled.setViewportSize({ width: 1280, height: 844 });
      await photosCentered(scrolled);
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
        await scrolled.locator(".total").filter({ hasText: "$ 141" }).waitFor();
        assert.equal(await input.evaluate(node => node === window.qaQuantityNode && node === document.activeElement), true);
        assert.ok(Math.abs(await scrolled.evaluate(() => scrollY) - desktopScroll) < 3);
        await scrolled.screenshot({ path: ".qa/screenshots/cart-desktop-scroll.png" });
      } finally { desktopRelease(); await scrolled.unrouteAll({ behavior: "wait" }); }
    } finally { unblock(); await isolated.close(); }
  });

  await t.test("carrito mayorista anterior se convierte al precio publicado; quitar mayorista no afecta importes", async () => {
    await page.evaluate(() => {
      const saved = JSON.parse(localStorage.getItem("dulce-salado.cart.v1"));
      saved.items[0].price_type = "wholesale";
      localStorage.setItem("dulce-salado.cart.v1", JSON.stringify(saved));
    });
    await page.reload();
    await waitCart("$ 300");
    await page.locator("#cart-notices").filter({ hasText: /ahora utiliza el precio publicado/ }).waitFor();
    assert.equal(await page.locator(".cart-price, .wholesale-note").count(), 0);
    assert.equal(JSON.parse(await page.evaluate(() => localStorage.getItem("dulce-salado.cart.v1"))).items[0].price_type, "retail");
    await editPrices("100", "");
    await page.reload();
    await waitCart("$ 300");
    assert.equal(await page.locator("#cart-review").isEnabled(), true);
    assert.equal(await page.locator("[data-cart-error]:visible, #cart-notices li").count(), 0);
  });

  await t.test("formulario accesible, Escape cancela y precio posterior exige nueva revisión", async () => {
    await page.locator("#cart-review").click();
    await page.locator("#cart-review-dialog[open]").waitFor();
    assert.equal(await page.locator("#review-title").innerText(), "Completá tus datos");
    assert.equal(await page.locator("#whatsapp-message, #copy-message").count(), 0);
    await accessible();
    await page.locator("#id_full_name").fill("Ana QA");
    await page.keyboard.press("Escape");
    await page.locator("#cart-review-dialog[open]").waitFor({ state: "hidden" });
    await page.locator("#cart-review:not([disabled])").waitFor();
    await page.locator("#cart-review").click();
    await page.locator("#id_full_name").waitFor();
    assert.equal(await page.locator("#id_full_name").inputValue(), "Ana QA");
    await editPrices("200", "90");
    const opening = page.waitForEvent("popup");
    await page.locator("#review-continue").click();
    const provisional = await opening;
    await page.locator("[data-review-required]").waitFor();
    if (!provisional.isClosed()) await provisional.waitForEvent("close");
    assert.equal(await page.locator("#id_full_name").inputValue(), "Ana QA");
    assert.equal(await page.locator("#review-continue").isDisabled(), true);
    await page.locator("#review-cancel").click();
    await waitCart("$ 600");
  });

  await t.test("cambio de unidad exige cantidad nueva y sincroniza pestañas", async () => {
    await admin.goto(`${base}/admin/catalog/product/${chocolateId}/change/`);
    await admin.locator("#id_sale_unit").selectOption("pack");
    await admin.locator('input[name="_save"]').click();
    await page.reload();
    await page.locator("[data-cart-error]").filter({ hasText: /Cambió la unidad de venta/ }).waitFor();
    assert.equal(await page.locator(".cart-quantity").inputValue(), "");
    assert.equal(await page.locator("#cart-review").isDisabled(), true);
    await setQuantity("2");
    await waitCart("$ 400");
    const second = await context.newPage();
    await second.goto(`${base}/carrito/`);
    await second.locator(".total").filter({ hasText: "$ 400" }).waitFor();
    await setQuantity("3");
    await second.locator(".total").filter({ hasText: "$ 600" }).waitFor();
    await waitCart("$ 600");
    await second.close();
  });

  await t.test("fallo de red oculta importes, recuperación y producto retirado", async () => {
    await page.route("**/carrito/recalcular/", route => route.abort());
    await page.reload();
    await page.locator("#cart-request-error").filter({ hasText: /Los importes no se muestran/ }).waitFor();
    assert.equal(await page.locator(".total").count(), 0);
    await page.unroute("**/carrito/recalcular/");
    await page.getByRole("button", { name: "Reintentar" }).click();
    await waitCart("$ 600");
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
    await blockedPage.locator(".catalog-increase").first().click();
    await blockedPage.getByRole("alert").filter({ hasText: /No se pudo guardar el carrito/ }).waitFor();
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

  await t.test("Ubicación desplegable, configuración Admin y Maps sólo por enlace", async () => {
    await page.goto(base);
    const panel = page.locator(".location-panel");
    const trigger = panel.locator("summary");
    await trigger.click();
    await page.getByText(/La dirección del comercio todavía no está disponible/).waitFor();
    assert.equal(await page.getByRole("link", { name: /Abrir en Google Maps/ }).count(), 0);
    assert.equal(new URL(page.url()).pathname, "/");
    await accessible();
    const address = "Dirección descartable de QA, no comercial";
    await admin.goto(`${base}/admin/catalog/businesssettings/add/`);
    await admin.locator("#id_address").fill(address);
    await admin.locator('input[name="_save"]').click();
    await admin.locator(".messagelist .success").waitFor();
    await page.reload();
    await trigger.press("Enter");
    assert.equal(await panel.locator("address").innerText(), address);
    const maps = panel.locator(".maps-link");
    const link = new URL(await maps.getAttribute("href"));
    assert.equal(link.searchParams.get("query"), address);
    assert.equal(link.searchParams.get("api"), "1");
    assert.equal(await maps.getAttribute("target"), "_blank");
    assert.equal(await maps.getAttribute("rel"), "noopener noreferrer");
    assert.equal(await maps.locator("svg.icon").count(), 1);
    assert.equal((await maps.textContent()).trim(), "");
    await page.mouse.move(0, 700);
    await maps.focus();
    assert.equal(await page.locator('iframe[src*="google"]').count(), 0);
    assert.equal(await page.locator(".brand small").count(), 0);
    for (const width of [320, 390, 768, 1050, 1280, 1440]) {
      await page.setViewportSize({ width, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const bounds = await panel.locator(".location-details").boundingBox();
      assert.ok(bounds.x >= 0 && bounds.x + bounds.width <= width);
      await page.screenshot({ path: `.qa/screenshots/header-location-${width}.png` });
      await accessible();
    }
    await page.keyboard.press("Escape");
    assert.equal(await panel.evaluate(node => node.open), false);
    assert.equal(await trigger.evaluate(node => node === document.activeElement), true);
    await trigger.press("Space");
    assert.equal(await panel.evaluate(node => node.open), true);
    await page.locator(".section-heading").click();
    assert.equal(await panel.evaluate(node => node.open), false);
    const footerMaps = page.locator(".footer-location");
    assert.equal(await footerMaps.getAttribute("href"), await maps.getAttribute("href"));
    assert.equal(await footerMaps.getAttribute("target"), "_blank");
    assert.equal(await footerMaps.getAttribute("rel"), "noopener noreferrer");
    const currentUrl = page.url();
    await context.route(url => url.hostname === "www.google.com" && url.pathname.startsWith("/maps"), route => route.fulfill({ contentType: "text/html", body: "<h1>Mapa interceptado de QA</h1>" }));
    const popupPromise = page.waitForEvent("popup");
    await footerMaps.click();
    const popup = await popupPromise;
    await popup.getByRole("heading", { name: "Mapa interceptado de QA" }).waitFor();
    await popup.close();
    assert.equal(page.url(), currentUrl);
    assert.equal(await panel.evaluate(node => node.open), false);
    for (const path of ["ubicacion/", "como-llegar/"]) {
      await page.goto(`${base}/${path}`);
      assert.equal(new URL(page.url()).pathname, "/");
      assert.equal(await panel.evaluate(node => node.open), true);
    }
    const plain = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 320, height: 844 } });
    const plainPage = await plain.newPage();
    await plainPage.goto(`${base}/ubicacion/`);
    assert.equal(await plainPage.locator(".location-panel").evaluate(node => node.open), true);
    assert.equal(await plainPage.locator("address").innerText(), address);
    await plainPage.locator(".location-panel summary").click();
    assert.equal(await plainPage.locator(".location-details").isVisible(), false);
    await plainPage.locator(".location-panel summary").click();
    assert.equal(await plainPage.locator(".location-details").isVisible(), true);
    await plain.close();
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
    for (const width of [320, 360, 390, 430, 768, 800, 1050, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      await page.locator(".hours-panel summary").hover();
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
      assert.ok(layout.height < (width >= 1050 ? 160 : 260));
      await headerLayout(width);
      assert.ok(layout.left >= 0 && layout.right <= width);
      await page.locator(".hours-details").hover();
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
    await page.locator(".location-panel summary").click();
    await page.waitForFunction(() => !document.querySelector(".hours-panel").open);
    assert.equal(await page.locator(".location-panel").evaluate(node => node.open), true);
    const plain = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 360, height: 844 } });
    const plainPage = await plain.newPage();
    await plainPage.goto(`${base}/ubicacion/`);
    await plainPage.locator(".hours-panel summary").click();
    assert.equal(await plainPage.locator(".weekly-hours").isVisible(), true);
    await plain.close();
    assert.deepEqual(errors, []);
  });

  await t.test("encabezado compacto conserva controles dentro del contenedor con fuentes distintas", async () => {
    const compact = await context.newPage();
    try {
      await compact.goto(base);
      await compact.locator(".hours-panel summary").waitFor();
      for (const font of ["monospace", "sans-serif"]) {
        await compact.locator(".header-actions").evaluate((node, font) => { node.style.fontFamily = font; }, font);
        for (const width of [320, 359, 360, 390, 399, 400, 600]) {
          await compact.setViewportSize({ width, height: 844 });
          const layout = await compact.locator(".header-actions").evaluate(node => {
            const bounds = node.closest(".header-inner").getBoundingClientRect();
            const controls = [...node.querySelectorAll("summary, .cart-link")].map(control => control.getBoundingClientRect()).filter(box => box.height);
            return { fits: controls.every(control => control.left >= bounds.left && control.right <= bounds.right),
              touch: controls.every(control => control.width >= 44 && control.height >= 44),
              scroll: document.documentElement.scrollWidth <= innerWidth };
          });
          assert.ok(layout.fits && layout.scroll, `Encabezado desbordado a ${width}px con ${font}`);
          assert.ok(layout.touch, `Control menor a 44px a ${width}px con ${font}`);
        }
      }
      await compact.setViewportSize({ width: 320, height: 844 });
      await compact.screenshot({ path: ".qa/screenshots/header-compact-320.png", fullPage: true });
      await accessible(compact);
    } finally { await compact.close(); }
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
    await page.locator(".catalog-increase").click();
    await page.goto(`${base}/carrito/`);
    await waitCart("$ 25");
    for (const width of [320, 360, 390, 430, 768, 800, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      const layout = await page.locator(".cart-item-heading").evaluate(node => {
        const name = node.querySelector("h2").getBoundingClientRect();
        const photo = node.querySelector(".cart-thumbnail").getBoundingClientRect();
        const row = node.closest(".cart-item"), plus = row.querySelector('[data-direction="1"]').getBoundingClientRect();
        return { separated: photo.right <= name.left && plus.right <= row.getBoundingClientRect().right,
          fits: document.documentElement.scrollWidth <= innerWidth };
      });
      assert.ok(layout.separated && layout.fits);
      if (width >= 800) await photosCentered(page);
      await page.locator(".cart-thumbnail").click();
      await page.keyboard.press("Escape");
      await page.screenshot({ path: `.qa/screenshots/cart-long-name-${width}.png`, fullPage: true });
      await accessible();
    }
    await page.getByRole("button", { name: /Aumentar cantidad/ }).click();
    await waitCart("$ 50");
    await photosCentered(page);
    await page.locator(".cart-thumbnail").click();
    await page.getByRole("button", { name: "Cerrar imagen" }).click();
    assert.equal(await page.locator(".cart-thumbnail").evaluate(node => node === document.activeElement), true);
    assert.equal(await page.evaluate(() => /image|media|\.webp/.test(localStorage.getItem("dulce-salado.cart.v1"))), false);
    await admin.goto(`${base}/admin/catalog/product/${id}/change/`);
    await admin.locator('input[name="image-clear"]').check();
    await admin.locator('input[name="_save"]').click();
    await admin.locator(".messagelist .success").waitFor();
    await page.reload();
    await waitCart("$ 50");
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
    await page.getByRole("button", { name: /Reducir cantidad de QA Velas/ }).click();
    await waitCart("$ 25");
    await page.getByRole("button", { name: /Quitar QA Velas/ }).click();
    await page.getByRole("heading", { name: "Tu carrito está vacío" }).waitFor();
    assert.deepEqual(errors, []);
  });

  await t.test("45 fixtures demo: tres páginas, filtros y GET sin JavaScript", async () => {
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
          form: { csrfmiddlewaretoken: token, category: id, name: name, brand: `Marca Demo ${category}`,
            description: "Semilla QA. Producto ficticio para pruebas aisladas.", sale_unit: unit, quantity_step: step,
            retail_price: retail, wholesale_price: wholesale || "", wholesale_condition: condition, is_active: "on", _save: "Guardar" },
        });
        assert.equal(result.url(), `${base}/admin/catalog/product/`);
      }
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${base}/?q=${encodeURIComponent("Semilla QA")}`);
    const seen = [];
    for (const [number, start, end] of [[1, 1, 20], [2, 21, 40], [3, 41, 45]]) {
      await page.getByText(`${start}–${end} de 45 productos`, { exact: false }).waitFor();
      assert.equal(await page.locator(".product-card").count(), end - start + 1);
      await page.getByText(`Página ${number} de 3`, { exact: true }).waitFor();
      seen.push(...await page.locator(".product-card").evaluateAll(nodes => nodes.map(node => node.getAttribute("aria-labelledby"))));
      for (const [width, columns] of [[1920, 5], [1440, 5], [1280, 4], [390, 2], [320, 2]]) {
        await page.setViewportSize({ width, height: 1080 });
        const rows = await page.locator(".product-card").evaluateAll(cards => {
          const rows = [];
          cards.forEach(card => {
            const y = card.getBoundingClientRect().top;
            const row = rows.find(row => Math.abs(row.y - y) < 1);
            if (row) row.count++; else rows.push({ y, count: 1 });
          });
          return rows.map(row => row.count);
        });
        assert.equal(rows[0], columns);
        if (number < 3 || columns === 5) assert.ok(rows.every(count => count === columns), `Fila incompleta: página ${number}, ${width}px`);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
        if (width === 1920) await page.screenshot({ path: `.qa/screenshots/full-five-columns-page-${number}.png`, fullPage: true });
      }
      if (number < 3) {
        await page.getByRole("link", { name: "Siguiente", exact: true }).click();
        await page.waitForURL(url => url.searchParams.get("page") === String(number + 1));
        assert.equal(new URL(page.url()).searchParams.get("q"), "Semilla QA");
      }
    }
    assert.equal(new Set(seen).size, 45);
    assert.equal(await page.getByRole("link", { name: "Siguiente", exact: true }).count(), 0);
    await page.getByRole("link", { name: "Anterior", exact: true }).click();
    await page.waitForURL(url => url.searchParams.get("page") === "2");
    for (const width of [360, 390, 430, 768, 1280]) {
      await page.setViewportSize({ width, height: 844 });
      await page.goto(`${base}/?q=${encodeURIComponent("Semilla QA")}`);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const targets = await page.locator(".pagination a").evaluateAll(nodes => nodes.map(node => node.getBoundingClientRect().height));
      assert.ok(targets.every(height => height >= 44));
      await page.screenshot({ path: `.qa/screenshots/demo-catalog-${width}.png`, fullPage: true });
      await page.locator(".pagination").screenshot({ path: `.qa/screenshots/demo-pagination-${width}.png` });
      await accessible();
    }
    await page.setViewportSize({ width: 390, height: 844 });
    for (const [category, slug] of Object.entries(slugs)) {
      const count = groups[category].length;
      await page.goto(`${base}/?q=${encodeURIComponent("Semilla QA")}&categoria=${slug}`);
      await page.getByText(`1–${Math.min(20, count)} de ${count} productos`, { exact: false }).waitFor();
      if (count > 20) {
        await page.getByRole("link", { name: "Siguiente", exact: true }).click();
        await page.waitForURL(url => url.searchParams.get("page") === "2");
        assert.equal(new URL(page.url()).searchParams.get("categoria"), slug);
        assert.equal(await page.locator(".product-card").count(), Math.min(20, count - 20));
      }
    }
    const plain = await browser.newContext({ javaScriptEnabled: false });
    const plainPage = await plain.newPage();
    await plainPage.goto(`${base}/?q=${encodeURIComponent("Semilla QA")}&categoria=reposteria`);
    await plainPage.getByRole("link", { name: "Siguiente", exact: true }).click();
    await plainPage.getByText("21–30 de 30 productos", { exact: false }).waitFor();
    assert.equal(new URL(plainPage.url()).searchParams.get("q"), "Semilla QA");
    await plain.close();
    assert.deepEqual(errors, []);
  });
});



test("Presentaciones compactas: sincronización, precio publicado, errores y alta repetida", { timeout: 60000 }, async t => {
  const browser = await chromium.launch();
  t.after(() => browser.close());
  t.diagnostic("Presentaciones: Chromium iniciado.");
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const setup = await context.newPage();
  setup.setDefaultTimeout(15000);
  await setup.goto(`${base}/admin/login/`);
  await setup.locator("#id_username").fill("qa-admin");
  await setup.locator("#id_password").fill("qa-only-password-582");
  await setup.locator('input[type="submit"]').click();
  await setup.locator("#user-tools").waitFor();
  t.diagnostic("Presentaciones: sesión Admin confirmada.");
  await setup.goto(`${base}/admin/catalog/product/add/`);
  await setup.locator("#id_category").selectOption({ label: "QA Repostería (test)" });
  await setup.locator("#id_name").fill("QA Compacto independiente");
  await setup.locator("#id_description").fill("Chips de chocolate, 500 gr");
  await setup.locator("#id_sale_unit").selectOption("paquete");
  await setup.locator("#id_retail_price").fill("100");
  await setup.locator("#id_wholesale_price").fill("90");
  await setup.locator('input[name="_save"]').click();
  // No cerrar la página con el POST pendiente: podría cancelar el alta del fixture.
  await setup.locator(".messagelist .success").waitFor();
  t.diagnostic("Presentaciones: fixture confirmado por Admin.");
  await setup.close();
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  await page.goto(`${base}/?q=QA%20Compacto%20independiente`);
  const card = page.locator(".product-card").first();
  const control = card.locator(".add-product");
  const id = await control.getAttribute("data-id");
  const unit = await control.getAttribute("data-unit");

  await t.test("resultado único acotado y controles táctiles compactos", async () => {
    assert.equal(await page.locator(".product-card").count(), 1);
    assert.ok((await card.boundingBox()).width <= 300);
    assert.equal(await card.locator(".product-category, .product-brand, select, input:not(.catalog-amount)").count(), 0);
    for (const width of [320, 360, 390, 430, 768, 1024, 1440, 1920]) {
      await page.setViewportSize({ width, height: 900 });
      assert.ok((await card.boundingBox()).width <= 340);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      const button = await card.locator(".catalog-increase").boundingBox();
      assert.ok(button.width >= 44 && button.height >= 44);
      assert.equal(await card.evaluate(node => {
        const info = node.querySelector(".product-info"), box = info.getBoundingClientRect();
        const plus = node.querySelector(".catalog-increase").getBoundingClientRect();
        return Math.abs(box.right - parseFloat(getComputedStyle(info).paddingRight) - plus.right) < 1;
      }), true);
    }
    await card.locator(".catalog-increase").press("Enter");
    assert.equal(await card.locator(".catalog-amount").inputValue(), "1");
    await page.screenshot({ path: ".qa/screenshots/presentation-single-desktop.png" });
  });

  await t.test("respuesta antigua no restaura un producto eliminado en otra pestaña", async () => {
    const stale = await context.newPage();
    // Simular entrega tardía de storage en una pestaña de fondo.
    await stale.addInitScript(() => window.addEventListener("storage", event => event.stopImmediatePropagation(), true));
    let release, ready;
    const held = new Promise(resolve => { release = resolve; });
    const received = new Promise(resolve => { ready = resolve; });
    await stale.route("**/carrito/recalcular/", async route => {
      const response = await route.fetch();
      ready();
      await held;
      await route.fulfill({ response });
    });
    try {
      await stale.goto(`${base}/carrito/`);
      await received;
      await page.bringToFront();
      await card.locator(".catalog-decrease").press("Enter");
      assert.equal(JSON.parse(await page.evaluate(() => localStorage.getItem("dulce-salado.cart.v1"))).items.length, 0);
      release();
      await stale.getByRole("heading", { name: "Tu carrito está vacío" }).waitFor();
      assert.equal(JSON.parse(await stale.evaluate(() => localStorage.getItem("dulce-salado.cart.v1"))).items.length, 0);
      assert.equal(await card.locator(".catalog-decrease").isVisible(), false);
    } finally { release(); await stale.close(); }
    await card.locator(".catalog-increase").click();
  });

  await t.test("carrito, catálogo y otra pestaña conservan cantidades y precio publicado", async () => {
    const other = await context.newPage();
    const errors = [];
    other.on("pageerror", error => errors.push(error.message));
    await other.goto(`${base}/carrito/`);
    await other.locator("#cart-contents:not([aria-busy]) .total").waitFor();
    const left = other.locator('.cart-adjust[data-direction="-1"]');
    const plus = other.locator('.cart-adjust[data-direction="1"]');
    assert.equal(await left.locator(".trash-icon").isVisible(), true);
    assert.equal(await left.locator(".cart-minus").isVisible(), false);
    assert.equal(await other.locator(".cart-quantity").inputValue(), "1");
    await other.screenshot({ path: ".qa/screenshots/cart-compact-trash.png", fullPage: true });
    // A mouse click keeps the input connected and updates its value as well as the total.
    await other.locator(".cart-quantity").focus();
    await plus.click();
    await other.locator("#cart-contents:not([aria-busy]) .total").filter({ hasText: "$ 200" }).waitFor();
    assert.equal(await other.locator(".cart-quantity").inputValue(), "2");
    assert.equal(await left.locator(".trash-icon").isVisible(), false);
    assert.equal(await left.locator(".cart-minus").isVisible(), true);
    await other.screenshot({ path: ".qa/screenshots/cart-compact-minus.png", fullPage: true });
    await left.press("Enter");
    await other.locator("#cart-contents:not([aria-busy]) .total").filter({ hasText: "$ 100" }).waitFor();
    assert.equal(await left.locator(".trash-icon").isVisible(), true);
    assert.equal(await left.locator(".cart-minus").isVisible(), false);
    await other.locator(".cart-quantity").fill("3");
    assert.equal(await left.locator(".cart-minus").isVisible(), true);
    await left.click();
    await other.locator("#cart-contents:not([aria-busy]) .total").filter({ hasText: "$ 200" }).waitFor();
    assert.equal(await other.locator(".cart-quantity").inputValue(), "2");
    await left.click();
    await other.locator("#cart-contents:not([aria-busy]) .total").filter({ hasText: "$ 100" }).waitFor();
    assert.equal(await left.locator(".trash-icon").isVisible(), true);
    await other.locator(".cart-quantity").fill("2");
    await other.locator(".cart-quantity").dispatchEvent("change");
    await other.locator("#cart-contents:not([aria-busy]) .total").filter({ hasText: "$ 200" }).waitFor();
    await other.locator(".cart-quantity").fill("1");
    await left.click();
    await other.getByRole("heading", { name: "Tu carrito está vacío" }).waitFor();
    await page.bringToFront();
    await card.locator(".catalog-increase").click();
    await other.locator("#cart-contents:not([aria-busy]) .total").filter({ hasText: "$ 100" }).waitFor();
    await page.bringToFront();
    await card.locator(".catalog-increase").click();
    const saved = JSON.parse(await page.evaluate(() => localStorage.getItem("dulce-salado.cart.v1")));
    assert.equal(saved.items[0].quantity, "2.00");
    assert.equal(saved.items[0].price_type, "retail");
    await other.locator('.cart-quantity').waitFor();
    await other.waitForFunction(() => Number(document.querySelector(".cart-quantity").value) === 2);
    await other.locator(".cart-quantity").fill("3");
    await other.locator(".cart-quantity").dispatchEvent("change");
    await other.locator("#cart-contents:not([aria-busy]) .total").waitFor();
    await page.bringToFront();
    await page.waitForFunction(() => document.querySelector(".catalog-amount").value === "3");
    await card.locator(".catalog-decrease").click();
    await card.locator(".catalog-decrease").click();
    assert.equal(await card.locator(".catalog-trash").isVisible(), true);
    assert.equal(await card.locator(".catalog-minus").isVisible(), false);
    await card.locator(".catalog-decrease").press("Enter");
    await page.getByRole("status").filter({ hasText: "Producto eliminado" }).waitFor();
    assert.equal(await card.locator(".catalog-decrease").isVisible(), false);
    await other.getByRole("heading", { name: "Tu carrito está vacío" }).waitFor();
    assert.deepEqual(errors, []);
    await other.close();
  });

  await t.test("fallo de escritura no agrega ni cambia la cantidad visible", async () => {
    await page.evaluate(() => {
      window.qaSetItem = Storage.prototype.setItem;
      Storage.prototype.setItem = () => { throw new DOMException("QA quota", "QuotaExceededError"); };
    });
    await card.locator(".catalog-increase").click();
    await page.getByRole("alert").filter({ hasText: "No se pudo guardar" }).waitFor();
    assert.equal(await card.locator(".catalog-amount").isVisible(), false);
    assert.equal(JSON.parse(await page.evaluate(() => localStorage.getItem("dulce-salado.cart.v1"))).items.length, 0);
    await page.evaluate(() => { Storage.prototype.setItem = window.qaSetItem; });
    await card.locator(".catalog-increase").click();
    assert.equal(await card.locator(".catalog-amount").inputValue(), "1");
    await page.reload();
    assert.equal(await card.locator(".catalog-amount").inputValue(), "1");
    assert.equal(await card.locator(".catalog-error").isVisible(), false);
    const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    assert.deepEqual(axe.violations.map(v => v.id), []);
  });

  await t.test("Guardar y agregar otro precarga una nueva ficha editable", async () => {
    const admin = await context.newPage();
    await admin.goto(`${base}/admin/catalog/product/add/`);
    assert.deepEqual(await admin.locator("#id_sale_unit option").evaluateAll(nodes => nodes.map(n => n.value)),
      ["100 gr", "kg", "caja", "pack", "paquete", "bolsa"]);
    assert.equal(await admin.locator('input[name="_continue"], #id_quantity_step').count(), 0);
    await admin.locator("#id_category").selectOption({ label: "QA Repostería (test)" });
    await admin.locator("#id_name").fill("QA Presentación repetida");
    await admin.locator("#id_brand").fill("Marca QA");
    await admin.locator("#id_description").fill("Chips 500 gr");
    await admin.locator("#id_sale_unit").selectOption("paquete");
    await admin.locator("#id_retail_price").fill("100");
    await admin.locator('input[name="_addanother"]').click();
    await admin.waitForURL(url => url.searchParams.has("copy"));
    assert.equal(await admin.locator("#id_name").inputValue(), "QA Presentación repetida");
    assert.equal(await admin.locator("#id_brand").inputValue(), "Marca QA");
    assert.equal(await admin.locator("#id_description").inputValue(), "Chips 500 gr");
    assert.equal(Number(await admin.locator("#id_retail_price").inputValue()), 100);
    await admin.locator("#id_description").fill("Chips 1 kg");
    await admin.locator("#id_retail_price").fill("180");
    await admin.locator('input[name="_save"]').click();
    await page.goto(`${base}/?q=QA%20Presentación%20repetida`);
    assert.equal(await page.locator(".product-card").count(), 2);
    assert.notEqual(...await page.locator(".add-product").evaluateAll(nodes => nodes.map(n => n.dataset.id)));
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: ".qa/screenshots/presentation-variants-mobile.png", fullPage: true });
    await admin.close();
  });
});


test("Mensaje editable en Administración: emojis, validación, revisión y enlace", { timeout: 60000 }, async t => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
  const admin = await context.newPage();
  const errors = [];
  admin.on("pageerror", error => errors.push(error.message));
  let originalMessage, originalProduct, settingsUrl;
  try {
    await admin.goto(`${base}/admin/login/`);
    await admin.locator("#id_username").fill("qa-admin");
    await admin.locator("#id_password").fill("qa-only-password-582");
    await admin.locator('input[type="submit"]').click();
    await admin.goto(`${base}/admin/catalog/businesssettings/`);
    const existing = admin.locator("#result_list tbody th a");
    if (await existing.count()) await existing.first().click();
    else await admin.locator(".object-tools .addlink").click();
    originalMessage = await admin.locator("#id_whatsapp_message_template").inputValue();
    originalProduct = await admin.locator("#id_whatsapp_product_template").inputValue();
    const productFormat = "{numero}. 🛍️ {producto}\n{descripcion}\n🏷️ Marca: {marca}\n• {cantidad} {unidad} × {precio}\nSubtotal: {subtotal}\n────────────";
    const generalFormat = "Hola de prueba 👋\n\n{productos}\n\n💰 Total de prueba: {total}\nGracias 🍫";
    const save = async () => {
      await admin.locator('input[name="_save"]').click();
      await admin.locator(".messagelist .success").waitFor();
    };

    await t.test("editor rechaza campos faltantes y guarda emojis; vista previa accesible", async () => {
      assert.match(originalMessage, /🛍️/);
      assert.match(originalMessage, /\*💰 Total:/);
      await admin.locator("#id_whatsapp_message_template").fill("{productos}");
      await admin.locator('input[name="_save"]').click();
      await admin.getByText(/Conservá estos campos/).waitFor();
      await admin.locator("#id_whatsapp_message_template").fill(generalFormat);
      await admin.locator("#id_whatsapp_product_template").fill(productFormat);
      await save();
      await admin.goto(`${base}/admin/catalog/businesssettings/1/change/`);
      settingsUrl = admin.url();
      assert.equal(await admin.locator("#id_whatsapp_message_template").inputValue(), generalFormat);
      assert.equal(await admin.locator("#id_whatsapp_product_template").inputValue(), productFormat);
      const preview = admin.locator(".field-message_preview pre");
      assert.match(await preview.innerText(), /Hola de prueba 👋/);
      assert.match(await preview.innerText(), /💰 Total de prueba: \$ 9\.100/);
      assert.equal(await admin.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const axe = await new AxeBuilder({ page: admin }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
      assert.deepEqual(axe.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) })), []);
      await admin.screenshot({ path: ".qa/screenshots/whatsapp-admin-editor-390.png", fullPage: true });
    });

    const page = await context.newPage();
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(base);
    assert.equal(await page.locator(".catalog-bar").getByRole("link", { name: "Catálogo", exact: true }).count(), 0);
    await page.locator(".catalog-increase").first().click();
    await page.goto(`${base}/carrito/`);
    await page.locator("#cart-review").click();
    await page.locator("#cart-review-dialog[open]").waitFor();

    await t.test("formulario conserva datos y exige nueva revisión del formato editable", async () => {
      await page.locator("#id_full_name").fill("Ana plantilla QA");
      await admin.locator("#id_whatsapp_message_template").fill(generalFormat.replace("Hola de prueba 👋", "Mensaje actualizado ✅"));
      await save();
      let destination;
      await context.route(/^https:\/\/api\.whatsapp\.com\/send\?/, async route => {
        destination = route.request().url();
        await route.fulfill({ contentType: "text/html", body: "<h1>WhatsApp interceptado</h1>" });
      });
      const first = page.waitForEvent("popup");
      await page.locator("#review-continue").click();
      const provisional = await first;
      await page.locator("[data-review-required]").waitFor();
      if (!provisional.isClosed()) await provisional.waitForEvent("close");
      assert.equal(destination, undefined);
      assert.equal(await page.locator("#id_full_name").inputValue(), "Ana plantilla QA");
      await page.locator("#review-cancel").click();
      await page.locator("#cart-review:not([disabled])").waitFor();
      await page.locator("#cart-review").click();
      await page.locator("#id_full_name").waitFor();
      const next = page.waitForEvent("popup");
      await page.locator("#review-continue").click();
      const whatsapp = await next;
      await whatsapp.getByRole("heading", { name: "WhatsApp interceptado" }).waitFor();
      const message = new URL(destination).searchParams.get("text");
      assert.match(message, /Mensaje actualizado ✅/);
      assert.match(message, /1\. 🛍️/);
      assert.match(message, /Gracias 🍫/);
      assert.match(message, /Ana plantilla QA/);
      assert.equal(new URL(await page.locator("#whatsapp-ready").getAttribute("href")).searchParams.get("text"), message);
      await whatsapp.close();
      assert.deepEqual(errors, []);
    });

  } finally {
    if (settingsUrl) {
      await admin.goto(settingsUrl);
      await admin.locator("#id_whatsapp_message_template").fill(originalMessage);
      await admin.locator("#id_whatsapp_product_template").fill(originalProduct);
      await admin.locator('input[name="_save"]').click();
    }
    await browser.close();
  }
});

test("Encabezado: espacio, paneles por mouse, teclado y toque", { timeout: 60000 }, async t => {
  const browser = await chromium.launch();
  t.after(() => browser.close());
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const admin = await context.newPage();
  await admin.goto(`${base}/admin/login/`);
  await admin.locator("#id_username").fill("qa-admin");
  await admin.locator("#id_password").fill("qa-only-password-582");
  await admin.locator('input[type="submit"]').click();
  await admin.goto(`${base}/admin/catalog/businesssettings/1/change/`);
  if (!await admin.locator("#id_address").count()) await admin.goto(`${base}/admin/catalog/businesssettings/add/`);
  await admin.locator("#id_address").fill("Dirección descartable de QA, no comercial");
  await admin.locator("#id_hours_initialized").check();
  await admin.locator("#id_opening_intervals-0-weekday").selectOption("0");
  await admin.locator("#id_opening_intervals-0-opens_at").fill("09:00");
  await admin.locator("#id_opening_intervals-0-closes_at").fill("12:00");
  await admin.locator('input[name="_save"]').click();
  await admin.locator(".messagelist .success").waitFor();
  await admin.close();
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(base);
  const location = page.locator(".location-panel"), hours = page.locator(".hours-panel");
  const summaries = [location.locator("summary"), hours.locator("summary")];
  async function opened(panel, value) { await page.waitForFunction(([selector, expected]) => document.querySelector(selector).open === expected, [await panel.getAttribute("class").then(name => `.${name}`), value]); }

  await t.test("buscador acotado, acciones cómodas y categorías sin íconos", async () => {
    assert.equal(await page.locator(".categories svg, .category-icon").count(), 0);
    assert.equal(await page.locator(".maps-link svg.icon").count(), 1);
    assert.equal(await page.locator(".location-panel").getByText("📍", { exact: true }).count(), 0);
    for (const width of [1050, 1280, 1440, 1920]) {
      await page.setViewportSize({ width, height: 900 });
      const bounds = await page.locator("header").evaluate(header => {
        const search = header.querySelector(".search-form").getBoundingClientRect();
        const actions = [...header.querySelectorAll(".header-control, .cart-link")].map(node => ({ ...node.getBoundingClientRect().toJSON(), font: parseFloat(getComputedStyle(node).fontSize) })).filter(box => box.height).sort((left, right) => left.left - right.left);
        return { search: search.toJSON(), actions };
      });
      assert.ok(bounds.search.width <= 600);
      assert.ok(bounds.actions.every(action => action.height >= 48));
      assert.ok(bounds.actions.slice(0, 2).every(action => action.font >= 15 && action.width >= 120));
      assert.ok(bounds.actions[2].width >= 64);
      assert.ok(bounds.actions[1].left - bounds.actions[0].right >= 16);
      assert.ok(bounds.actions[2].left - bounds.actions[1].right >= 16);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    }
    await page.setViewportSize({ width: 1440, height: 900 });
  });

  await t.test("hover cruza al panel, cierra al salir, mantiene foco y flecha fija", async () => {
    await page.mouse.move(0, 800);
    for (const [panel, summary] of [[location, summaries[0]], [hours, summaries[1]]]) {
      await summary.hover();
      await opened(panel, true);
      assert.equal(await summary.locator(".disclosure-arrow").evaluate(node => getComputedStyle(node).transform), "none");
      assert.equal(await summary.locator(".disclosure-arrow path").getAttribute("d"), "m6 9 6 6 6-6");
      assert.equal(await summary.evaluate(node => node === document.activeElement), false);
      await panel.locator(".header-panel-content").hover();
      await page.waitForTimeout(250);
      assert.equal(await panel.evaluate(node => node.open), true);
      await page.mouse.move(0, 800);
      await opened(panel, false);
      assert.equal(await summary.locator(".disclosure-arrow").evaluate(node => getComputedStyle(node).transform), "none");
    }
    await summaries[0].hover();
    await summaries[1].hover();
    await opened(location, false);
    await opened(hours, true);
    await page.keyboard.press("Escape");
    await opened(hours, false);
    await page.waitForTimeout(250);
    assert.equal(await hours.evaluate(node => node.open), false);
    assert.equal(await summaries[1].evaluate(node => node === document.activeElement), true);
    await page.mouse.move(0, 800);
    await summaries[0].hover();
    await page.locator(".maps-link").focus();
    await page.mouse.move(0, 800);
    await page.waitForTimeout(250);
    assert.equal(await location.evaluate(node => node.open), true);
    await page.keyboard.press("Tab");
    await opened(location, false);
    await summaries[1].press("Enter");
    await opened(hours, true);
    await page.keyboard.press("Escape");
    await opened(hours, false);
    await summaries[0].click();
    await opened(location, true);
    await page.mouse.move(0, 800);
    await opened(location, false);
    const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    assert.deepEqual(axe.violations.map(v => v.id), []);
  });

  await t.test("pantalla táctil conserva abrir/cerrar por toque y el cierre exterior", async () => {
    const touch = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    const mobile = await touch.newPage();
    await mobile.goto(base);
    assert.equal(await mobile.evaluate(() => matchMedia("(hover: hover) and (pointer: fine)").matches), false);
    for (const selector of [".location-panel", ".hours-panel"]) {
      const panel = mobile.locator(selector), summary = panel.locator("summary");
      await summary.tap();
      assert.equal(await panel.evaluate(node => node.open), true);
      await summary.tap();
      assert.equal(await panel.evaluate(node => node.open), false);
      await summary.tap();
      await mobile.locator("#catalog-search").tap();
      assert.equal(await panel.evaluate(node => node.open), false);
    }
    await touch.close();
    assert.deepEqual(errors, []);
  });
});

test("Carrito lateral en iframe: apertura, scroll, revisión y retorno", { timeout: 90000 }, async t => {
  const browser = await chromium.launch();
  t.after(() => browser.close());
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(base);
  const drawer = page.locator("#cart-drawer"), frame = page.frameLocator("#cart-drawer iframe");
  const cartLink = page.locator(".cart-link");
  async function open() {
    await cartLink.click();
    await page.locator("#cart-drawer[open]").waitFor();
    await frame.locator("#cart-contents:not([aria-busy]) .empty-state, #cart-contents:not([aria-busy]) .cart-layout").first().waitFor();
  }
  async function close() { await drawer.locator(".cart-drawer-close").click(); await page.locator("#cart-drawer[open]").waitFor({ state: "hidden" }); }

  await t.test("buscador sin contorno al clicar y ubicación centrada sin desbordar", async () => {
    const search = page.locator("#catalog-search");
    await search.click();
    assert.equal(await search.evaluate(node => getComputedStyle(node).outlineStyle), "none");
    assert.equal(await page.locator(".search-form").evaluate(node => getComputedStyle(node).outlineStyle), "none");
    await page.locator(".brand").focus();
    await page.keyboard.press("Tab");
    assert.equal(await search.evaluate(node => node === document.activeElement), true);
    assert.equal(await page.locator(".search-form").evaluate(node => getComputedStyle(node).outlineStyle), "solid");
    for (const width of [320, 390, 768, 1050, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      await page.locator(".location-panel summary").hover();
      const geometry = await page.locator(".location-panel").evaluate(panel => {
        const trigger = panel.querySelector("summary").getBoundingClientRect();
        const popup = panel.querySelector(".location-details").getBoundingClientRect();
        return { left: popup.left, right: popup.right, center: popup.x + popup.width / 2, expected: Math.max(16 + popup.width / 2, Math.min(trigger.x + trigger.width / 2, innerWidth - 16 - popup.width / 2)) };
      });
      assert.ok(Math.abs(geometry.center - geometry.expected) < 1);
      assert.ok(geometry.left >= 15 && geometry.right <= width - 15);
      await page.keyboard.press("Escape");
      await page.mouse.move(0, 899);
    }
    await page.setViewportSize({ width: 1440, height: 900 });
  });

  await t.test("vacío abre sin navegar ni mover catálogo; agregar productos cierra", async () => {
    const before = await page.locator(".product-card").first().boundingBox();
    const url = page.url();
    await open();
    assert.equal(page.url(), url);
    const after = await page.locator(".product-card").first().boundingBox();
    assert.deepEqual(after, before);
    const bounds = await drawer.boundingBox();
    assert.ok(Math.abs(bounds.width - 1440 * .46) < 1);
    assert.equal(bounds.x + bounds.width, 1440);
    assert.equal(bounds.height, 900);
    assert.notEqual(await drawer.evaluate(node => getComputedStyle(node, "::backdrop").backdropFilter), "none");
    assert.equal(await frame.locator("#cart-review").count(), 0);
    await frame.getByRole("button", { name: "Agregar productos", exact: true }).click();
    await page.locator("#cart-drawer[open]").waitFor({ state: "hidden" });
    assert.equal(await cartLink.evaluate(node => node === document.activeElement), true);
    await open();
    await page.mouse.click(20, 400);
    await page.locator("#cart-drawer[open]").waitFor({ state: "hidden" });
    await open();
    await frame.locator("body").press("Escape");
    await page.locator("#cart-drawer[open]").waitFor({ state: "hidden" });
  });

  await t.test("productos verticales, total fijo y cantidades sincronizadas al cerrar", async () => {
    const controls = page.locator(".catalog-increase");
    for (let index = 0; index < Math.min(10, await controls.count()); index++) await controls.nth(index).click();
    await open();
    assert.ok(await frame.locator(".cart-item").count() >= 10);
    const footerBefore = await frame.locator(".cart-summary").boundingBox();
    await frame.locator(".cart-items").evaluate(list => { list.scrollTop = list.scrollHeight; });
    assert.ok(await frame.locator(".cart-items").evaluate(list => list.scrollTop > 0));
    assert.deepEqual(await frame.locator(".cart-summary").boundingBox(), footerBefore);
    assert.equal(await frame.locator("#cart-review").isVisible(), true);
    const plus = frame.locator('.cart-adjust[data-direction="1"]').last();
    await plus.click();
    await frame.locator("#cart-contents:not([aria-busy]) .total").waitFor();
    assert.equal(await frame.locator(".cart-quantity").last().inputValue(), "2");
    const id = await frame.locator(".cart-item").last().getAttribute("data-id");
    await close();
    assert.equal(await page.locator(`.add-product[data-id="${id}"] .catalog-amount`).inputValue(), "2");
    await open();
    const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    assert.deepEqual(axe.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) })), []);
    await page.screenshot({ path: ".qa/screenshots/cart-drawer-1440.png" });
    await close();
  });

  await t.test("pantalla completa móvil, volver y revisión WhatsApp sin salir del catálogo", async () => {
    await page.setViewportSize({ width: 390, height: 844 });
    await open();
    assert.equal((await drawer.boundingBox()).width, 390);
    assert.equal(await drawer.locator(".drawer-back").isVisible(), true);
    assert.equal(await drawer.locator(".drawer-cross").isVisible(), false);
    await frame.locator("#cart-review").click();
    await frame.locator("#cart-review-dialog[open]").waitFor();
    assert.equal(await frame.locator("#review-title").innerText(), "Completá tus datos");
    await page.screenshot({ path: ".qa/screenshots/cart-drawer-review-390.png" });
    await frame.locator("#review-cancel").click();
    await frame.locator("#cart-review-dialog[open]").waitFor({ state: "hidden" });
    await close();
    assert.equal(new URL(page.url()).pathname, "/");
    await open();
    // Un mensaje originado en el padre no suplanta al iframe autorizado.
    await page.evaluate(() => postMessage({ type: "dys-cart-close" }, location.origin));
    assert.equal(await drawer.evaluate(node => node.open), true);
    await close();
    assert.deepEqual(errors, []);
  });
  await t.test("Escape vuelve del formulario y conserva los datos en el iframe", async () => {
    await open();
    await frame.locator("#cart-review").click();
    await frame.locator("#id_full_name").waitFor();
    await frame.locator("#id_full_name").fill("Ana iframe QA");
    await frame.locator("#id_full_name").press("Escape");
    await frame.locator("#cart-review-dialog[open]").waitFor({ state: "hidden" });
    assert.equal(await drawer.evaluate(node => node.open), true);
    await frame.locator("#cart-review:not([disabled])").waitFor();
    await frame.locator("#cart-review").click();
    await frame.locator("#id_full_name").waitFor();
    assert.equal(await frame.locator("#id_full_name").inputValue(), "Ana iframe QA");
    await frame.locator("#review-cancel").click();
    await close();
  });

  await t.test("toque móvil cierra con volver y Agregar productos sin navegar", async () => {
    const touch = await browser.newContext({ viewport: { width: 320, height: 700 }, isMobile: true, hasTouch: true });
    const mobile = await touch.newPage();
    await mobile.goto(base);
    await mobile.locator(".cart-link").tap();
    const content = mobile.frameLocator("#cart-drawer iframe");
    await content.getByRole("button", { name: "Agregar productos", exact: true }).tap();
    await mobile.locator("#cart-drawer[open]").waitFor({ state: "hidden" });
    await mobile.locator(".cart-link").tap();
    await mobile.locator(".cart-drawer-close").tap();
    await mobile.locator("#cart-drawer[open]").waitFor({ state: "hidden" });
    assert.equal(new URL(mobile.url()).pathname, "/");
    await touch.close();
    assert.deepEqual(errors, []);
  });

  await t.test("fallo al cargar el iframe conserva cierre y acceso de respaldo", async () => {
    await page.route("**/carrito/?panel=1", route => route.abort());
    await cartLink.click();
    await page.locator("#cart-drawer[open]").waitFor();
    await drawer.getByRole("link", { name: "Abrir carrito en otra pestaña" }).waitFor();
    await close();
    assert.equal(await page.locator("html").evaluate(node => node.classList.contains("cart-modal-open")), false);
    await page.unroute("**/carrito/?panel=1");
    assert.deepEqual(errors, []);
  });

  await t.test("Ver carrito desde el aviso conserva scroll y recupera foco al cerrar", async () => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(base);
    await page.locator(".catalog-increase").last().click();
    await page.evaluate(() => scrollTo(0, Math.max(0, document.documentElement.scrollHeight - innerHeight - 50)));
    const y = await page.evaluate(() => scrollY);
    assert.ok(y > 0);
    const before = await page.locator(".product-card").first().boundingBox();
    await page.getByRole("link", { name: "Ver carrito", exact: true }).click();
    await frame.locator("#cart-contents:not([aria-busy]) .cart-layout").waitFor();
    assert.equal(await page.evaluate(() => scrollY), y);
    assert.deepEqual(await page.locator(".product-card").first().boundingBox(), before);
    await close();
    assert.equal(await page.evaluate(() => scrollY), y);
    assert.equal(await cartLink.evaluate(node => node === document.activeElement), true);
    await open();
    for (let attempts = 0; attempts < 30 && await frame.locator(".cart-item").count(); attempts++) {
      await frame.locator('.cart-adjust[data-direction="-1"]').first().click();
      await frame.locator("#cart-contents:not([aria-busy])").waitFor();
    }
    assert.equal(await frame.locator(".cart-item").count(), 0);
    assert.equal(await frame.locator(".total").innerText(), "$ 0");
    assert.equal(await page.locator("[data-cart-count]").innerText(), "0");
    await frame.getByRole("button", { name: "Agregar productos", exact: true }).click();
    await page.locator("#cart-drawer[open]").waitFor({ state: "hidden" });
    assert.deepEqual(errors, []);
  });

});

test("Centrado de grilla y avisos; carrito más ancho", { timeout: 60000 }, async t => {
  const browser = await chromium.launch();
  t.after(() => browser.close());
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  await page.goto(base);

  await t.test("filas de una, dos y tres columnas centradas con igual altura", async () => {
    for (const width of [320, 390, 520, 600, 700, 740, 768, 800, 1000, 1050, 1280, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      const geometry = await page.locator(".product-grid").evaluate(grid => {
        const bounds = grid.getBoundingClientRect();
        const cards = [...grid.querySelectorAll(".product-card")].map(node => node.getBoundingClientRect().toJSON());
        const firstRow = cards.filter(card => Math.abs(card.top - cards[0].top) < 1);
        return { center: bounds.x + bounds.width / 2, left: Math.min(...firstRow.map(card => card.left)), right: Math.max(...firstRow.map(card => card.right)), row: firstRow };
      });
      assert.ok(Math.abs((geometry.left + geometry.right) / 2 - geometry.center) < 1, `Descentrado a ${width}px`);
      assert.ok(geometry.row.every(card => Math.abs(card.height - geometry.row[0].height) < 1));
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      if ([520, 740, 1000].includes(width)) await page.screenshot({ path: `.qa/screenshots/centered-grid-${width}.png` });
    }
  });

  await t.test("éxitos y errores arriba, texto centrado y acción inline cuando cabe", async () => {
    await page.setViewportSize({ width: 1440, height: 900 });
    for (const kind of ["success", "error"]) {
      await page.evaluate(kind => Notifications.show("Se agregó Chocolate al carrito.", kind, { label: "Ver carrito", href: "/carrito/" }), kind);
      const toast = page.locator("[data-notification]:visible");
      const bounds = await toast.boundingBox();
      assert.ok(Math.abs(bounds.x + bounds.width / 2 - 720) < 1);
      assert.ok(Math.abs(bounds.y - 16) < 1);
      assert.equal(await toast.locator("p").evaluate(node => getComputedStyle(node).textAlign), "center");
      const text = await toast.locator("p").boundingBox(), link = await toast.locator("a").boundingBox();
      assert.ok(Math.abs(text.y + text.height / 2 - link.y - link.height / 2) < 1);
      assert.ok(text.x + text.width <= link.x);
      await page.screenshot({ path: `.qa/screenshots/centered-notice-${kind}-1440.png` });
    }
    for (const width of [320, 390, 768]) {
      await page.setViewportSize({ width, height: 900 });
      await page.evaluate(() => Notifications.show("Nombre largo ".repeat(25), "error", { label: "Ver carrito", href: "/carrito/" }));
      const bounds = await page.locator("[data-notification]:visible").boundingBox();
      assert.ok(bounds.x >= 15 && bounds.x + bounds.width <= width - 15);
      assert.ok(Math.abs(bounds.y - 16) < 1);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
      assert.deepEqual(axe.violations.map(v => v.id), []);
    }
    await page.evaluate(() => Notifications.close());
  });

  await t.test("carrito cerca de media pantalla en escritorio y completo en móvil", async () => {
    await page.locator(".catalog-increase").first().click();
    await page.locator(".cart-link").click();
    const drawer = page.locator("#cart-drawer"), frame = page.frameLocator("#cart-drawer iframe");
    await frame.locator("#cart-contents:not([aria-busy]) .cart-item").first().waitFor();
    for (const width of [320, 390, 600, 768, 1050, 1280, 1440, 1920]) {
      await page.setViewportSize({ width, height: 900 });
      const bounds = await drawer.boundingBox();
      const expected = width <= 600 ? width : Math.max(520, width * .46);
      assert.ok(Math.abs(bounds.width - expected) < 1);
      assert.ok(Math.abs(bounds.x + bounds.width - width) < 1);
      assert.ok(await frame.locator("body").evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      assert.equal(await frame.locator("#cart-review").isVisible(), true);
    }
    await drawer.locator(".cart-drawer-close").click();
  });
});


test("Recalcular carrito conserva posiciones sin mensaje visible de consulta", { timeout: 30000 }, async t => {
  const browser = await chromium.launch();
  t.after(() => browser.close());
  for (const panel of [false, true]) {
    await t.test(panel ? "iframe: sumar y restar sin saltos" : "página directa: sumar y restar sin saltos", async () => {
      const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
      const page = await context.newPage();
      try {
        await page.goto(base);
        for (const button of (await page.locator(".catalog-increase").all()).slice(0, 3)) await button.click();
        await page.evaluate(() => Notifications.close());
        let cart;
        if (panel) {
          await page.locator(".cart-link").click();
          cart = page.frameLocator("#cart-drawer iframe");
        } else {
          await page.goto(`${base}/carrito/`);
          cart = page;
        }
        await cart.locator("#cart-contents:not([aria-busy]) .cart-item").first().waitFor();
        const geometry = () => cart.locator("#cart-app").evaluate(app => {
          const bounds = selector => {
            const rect = app.querySelector(selector).getBoundingClientRect();
            return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
          };
          return { contents: bounds("#cart-contents"), list: bounds(".cart-items"), first: bounds(".cart-item"), summary: bounds(".cart-summary") };
        });
        for (const direction of ["1", "-1"]) {
          const before = await geometry();
          let release, received;
          const held = new Promise(resolve => { release = resolve; });
          const ready = new Promise(resolve => { received = resolve; });
          const handler = async route => {
            const response = await route.fetch();
            received();
            await held;
            await route.fulfill({ response });
          };
          await page.route("**/carrito/recalcular/", handler);
          try {
            await cart.locator(`.cart-adjust[data-direction="${direction}"]`).first().click();
            await ready;
            await cart.locator('#cart-contents[aria-busy="true"]').waitFor();
            assert.deepEqual(await geometry(), before);
            const status = await cart.locator("#cart-loading").evaluate(node => ({
              height: node.getBoundingClientRect().height, width: node.getBoundingClientRect().width,
              position: getComputedStyle(node).position, clip: getComputedStyle(node).clipPath,
              text: node.textContent, role: node.getAttribute("role"),
            }));
            assert.deepEqual(status, { height: 1, width: 1, position: "absolute", clip: "inset(50%)", text: "Consultando el catálogo vigente…", role: "status" });
            assert.equal(await cart.locator("#cart-review").isDisabled(), true);
            assert.equal(await cart.locator("#cart-review").evaluate(node => getComputedStyle(node).opacity), "1");
            await page.screenshot({ path: `.qa/screenshots/cart-refresh-${panel ? "iframe" : "direct"}-${direction}.png` });
            release();
            await cart.locator("#cart-contents:not([aria-busy]) .cart-item").first().waitFor();
            assert.deepEqual(await geometry(), before);
            assert.equal(await cart.locator(".cart-quantity").first().inputValue(), direction === "1" ? "2" : "1");
            assert.equal(await cart.locator("#cart-review").isEnabled(), true);
          } finally {
            release();
            await page.unroute("**/carrito/recalcular/", handler);
          }
        }
        const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
        assert.deepEqual(axe.violations.map(v => v.id), []);
      } finally { await context.close(); }
    });
  }
});

test("Carrito silencioso y estable con muchos productos", { timeout: 60000 }, async t => {
  const browser = await chromium.launch();
  t.after(() => browser.close());
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage(), errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(base);
  let added = 0, lastName;
  const selected = new Set();
  for (let number = 1; number <= 5 && added < 2; number++) {
    await page.goto(`${base}/?page=${number}`);
    for (const control of await page.locator(".product-card:has(img) .add-product").all()) {
      const id = await control.getAttribute("data-id");
      if (selected.has(id)) continue;
      selected.add(id);
      lastName = await control.getAttribute("data-name");
      await control.locator(".catalog-increase").press("Enter");
      if (++added === 2) break;
    }
  }
  // Otras pruebas pueden haber retirado fotos; completar con otra ficha distinta.
  if (added < 2) {
    for (const control of await page.locator(".add-product").all()) {
      const id = await control.getAttribute("data-id");
      if (selected.has(id)) continue;
      selected.add(id);
      lastName = await control.getAttribute("data-name");
      await control.locator(".catalog-increase").press("Enter");
      if (++added === 2) break;
    }
  }
  assert.equal(added, 2);
  const drawer = page.locator("#cart-drawer"), cart = page.frameLocator("#cart-drawer iframe");
  const settled = () => cart.locator("#cart-contents:not([aria-busy]) .cart-item").first().waitFor();

  await t.test("nuevo mensaje, cruces acordes y apertura sin Cargando carrito", async () => {
    const notice = page.locator("[data-notification]:visible");
    assert.equal(await notice.locator("p").innerText(), `Se agregó ${lastName} al carrito.`);
    assert.equal(await notice.getByRole("link", { name: "Ver carrito", exact: true }).count(), 1);
    for (const kind of ["success", "error", "warning", "info"]) {
      await page.evaluate(kind => Notifications.show("Prueba de estilo", kind), kind);
      assert.equal(await notice.locator("button").evaluate(node => getComputedStyle(node).color), await notice.evaluate(node => getComputedStyle(node).color));
      assert.equal(await notice.locator("button").evaluate(node => getComputedStyle(node).borderColor), "rgba(0, 0, 0, 0)");
      assert.equal(await notice.locator("button svg").count(), 1);
    }
    await page.evaluate(() => Notifications.close());
    let release, arrived;
    const held = new Promise(resolve => { release = resolve; });
    const ready = new Promise(resolve => { arrived = resolve; });
    await page.route("**/carrito/?panel=1", async route => { const response = await route.fetch(); arrived(); await held; await route.fulfill({ response }); });
    try {
      await page.locator(".cart-link").click();
      await ready;
      assert.equal(await drawer.locator(".cart-drawer-loading").isVisible(), false);
      assert.equal(await drawer.getByText("Cargando carrito", { exact: false }).count(), 0);
      assert.equal(await drawer.locator("iframe").getAttribute("aria-busy"), "true");
      release();
      await settled();
    } finally { release(); await page.unroute("**/carrito/?panel=1"); }
  });

  await t.test("sólo cambia cantidad/subtotal/total; fotos y otras filas permanecen conectadas", async () => {
    await cart.locator("#cart-app").evaluate(app => {
      const rows = [...app.querySelectorAll(".cart-item")];
      window.qaStable = { document, images: [...app.querySelectorAll("img")], headings: rows.map(row => row.querySelector(".cart-item-heading")), row: rows[1], changes: [] };
      const observer = new MutationObserver(records => window.qaStable.changes.push(...records.map(record => ({type: record.type, attr: record.attributeName, tag: record.target.tagName, id: record.target.id, html: record.target.outerHTML}))));
      observer.observe(rows[1], { subtree: true, childList: true, attributes: true, characterData: true });
      window.qaStable.observer = observer;
    });
    let navigations = 0;
    const navigation = frame => { if (frame.parentFrame()) navigations++; };
    page.on("framenavigated", navigation);
    try {
      for (const [direction, expected] of [["1", "2"], ["1", "3"], ["-1", "2"], ["-1", "1"]]) {
        await cart.locator(`.cart-adjust[data-direction="${direction}"]`).first().click();
        await settled();
        assert.equal(await cart.locator(".cart-quantity").first().inputValue(), expected);
        assert.equal(await cart.locator("[data-notification]:visible").count(), 0);
        assert.equal(await cart.locator("#cart-app").evaluate(app => window.qaStable.document === document && window.qaStable.images.length >= 1 && window.qaStable.images.every(image => image.isConnected) && window.qaStable.headings.every(heading => heading.isConnected) && app.querySelectorAll(".cart-item")[1] === window.qaStable.row), true);
      }
      assert.equal(navigations, 0);
      assert.deepEqual(await cart.locator("#cart-app").evaluate(() => window.qaStable.changes), []);
    } finally { page.off("framenavigated", navigation); }
  });

  await t.test("eliminar no muestra aviso y conserva las demás fichas", async () => {
    await cart.locator('.cart-adjust[data-direction="-1"]').first().click();
    await cart.locator("#cart-contents:not([aria-busy]) .cart-item").waitFor();
    assert.equal(await cart.locator(".cart-item").count(), 1);
    assert.equal(await cart.locator("[data-notification]:visible").count(), 0);
    assert.equal(await cart.locator("#cart-app").evaluate(app => app.querySelector(".cart-item") === window.qaStable.row), true);
    await drawer.locator(".cart-drawer-close").click();
  });

  await t.test("lista larga sin filas comprimidas ni controles superpuestos en desktop/móvil", async () => {
    await page.goto(base);
    for (const button of await page.locator(".catalog-increase").all()) await button.press("Enter");
    await page.evaluate(() => Notifications.close());
    await page.locator(".cart-link").click();
    await settled();
    assert.ok(await cart.locator(".cart-item").count() >= 12);
    for (const width of [1920, 1440, 1050, 768, 390, 320]) {
      await page.setViewportSize({ width, height: 1080 });
      const geometry = await cart.locator(".cart-items").evaluate(list => {
        const rows = [...list.querySelectorAll(".cart-item")];
        return rows.every((row, index) => {
          const bounds = row.getBoundingClientRect();
          return (!index || rows[index - 1].getBoundingClientRect().bottom + 5 < bounds.top) && [...row.querySelectorAll(".product-controls, .cart-thumbnail")].every(node => { const child = node.getBoundingClientRect(); return child.top >= bounds.top && child.bottom <= bounds.bottom; });
        });
      });
      assert.equal(geometry, true, `Superposición a ${width}px`);
      const footer = await cart.locator(".cart-summary").boundingBox();
      await cart.locator(".cart-items").evaluate(list => { list.scrollTop = list.scrollHeight; });
      assert.ok(await cart.locator(".cart-items").evaluate(list => list.scrollTop > 0));
      assert.deepEqual(await cart.locator(".cart-summary").boundingBox(), footer);
      assert.equal(await cart.locator("body").evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await cart.locator(".cart-items").evaluate(list => { list.scrollTop = 0; });
      if ([1920, 390].includes(width)) await page.screenshot({ path: `.qa/screenshots/cart-many-no-overlap-${width}.png` });
    }
  });

  await t.test("formulario de datos compacto y accesible en el panel", async () => {
    for (const width of [1920, 390]) {
      await page.setViewportSize({ width, height: 1080 });
      await cart.locator("#cart-review").click();
      await cart.locator("#cart-review-dialog[open]").waitFor();
      assert.equal(await cart.locator("#review-title").innerText(), "Completá tus datos");
      assert.equal(await cart.locator("textarea, #copy-message").count(), 0);
      const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
      assert.deepEqual(axe.violations.map(v => v.id), []);
      await page.screenshot({ path: `.qa/screenshots/cart-customer-${width}.png` });
      await cart.locator("#review-cancel").click();
      await settled();
    }
    assert.deepEqual(errors, []);
  });


});

test("Zoom sin marco, revisión simple y cantidades enteras", { timeout: 60000 }, async t => {
  const browser = await chromium.launch();
  t.after(() => browser.close());
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage(), errors = [];
  page.on("pageerror", error => errors.push(error.message));
  let source;
  for (let number = 1; number <= 5; number++) {
    await page.goto(`${base}/?page=${number}`);
    if (await page.locator(".product-image-open").count()) { source = page.locator(".product-image-open").first(); break; }
  }
  assert.ok(source);
  const verifyZoom = async scope => {
    const geometry = await scope.locator("#product-image-dialog").evaluate(dialog => {
      const photo = dialog.querySelector("img"), close = dialog.querySelector("button");
      const p = photo.getBoundingClientRect(), c = close.getBoundingClientRect(), d = getComputedStyle(dialog), x = getComputedStyle(close);
      return { outside: c.bottom <= p.top || c.left >= p.right || c.right <= p.left || c.top >= p.bottom,
        contained: p.left >= 0 && p.right <= innerWidth && p.top >= 0 && p.bottom <= innerHeight,
        background: d.backgroundColor, border: d.borderTopWidth, closeColor: x.color, closeBackground: x.backgroundColor,
        closeBorder: x.borderTopWidth, backdrop: getComputedStyle(dialog, "::backdrop").backgroundColor,
        fit: getComputedStyle(photo).objectFit, width: c.width, height: c.height };
    });
    assert.equal(geometry.outside && geometry.contained, true);
    assert.equal(geometry.background, "rgba(0, 0, 0, 0)");
    assert.equal(geometry.border, "0px");
    assert.equal(geometry.closeColor, "rgb(255, 255, 255)");
    assert.equal(geometry.closeBackground, "rgba(0, 0, 0, 0)");
    assert.equal(geometry.closeBorder, "0px");
    assert.equal(geometry.backdrop, "rgba(0, 0, 0, 0.85)");
    assert.equal(geometry.fit, "contain");
    assert.ok(geometry.width >= 44 && geometry.height >= 44);
  };

  await t.test("catálogo: cruz blanca fuera de imagen, fondo oscuro y cierre accesible", async () => {
    for (const [width, height] of [[1920, 1080], [390, 844], [844, 300]]) {
      await page.setViewportSize({ width, height });
      await source.click();
      await page.locator("#product-image-expanded").evaluate(img => img.decode());
      await verifyZoom(page);
      const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
      assert.deepEqual(axe.violations.map(v => v.id), []);
      await page.screenshot({ path: `.qa/screenshots/zoom-clean-catalog-${width}.png` });
      await page.getByRole("button", { name: "Cerrar imagen", exact: true }).click();
      assert.equal(await source.evaluate(node => node === document.activeElement), true);
    }
  });

  await t.test("carrito: mismo visor externo a la foto y Escape vuelve al producto", async () => {
    const card = source.locator("xpath=ancestor::article");
    await card.locator(".catalog-increase").press("Enter");
    await page.evaluate(() => Notifications.close());
    await page.locator(".cart-link").click();
    const cart = page.frameLocator("#cart-drawer iframe");
    await cart.locator("#cart-contents:not([aria-busy]) .cart-thumbnail").waitFor();
    for (const width of [1920, 390]) {
      await page.setViewportSize({ width, height: 1080 });
      await cart.locator(".cart-thumbnail").click();
      await cart.locator("#product-image-expanded").evaluate(img => img.decode());
      await verifyZoom(cart);
      await page.screenshot({ path: `.qa/screenshots/zoom-clean-cart-${width}.png` });
      await cart.locator("#product-image-expanded").press("Escape");
      await cart.locator("#product-image-dialog[open]").waitFor({ state: "hidden" });
      assert.equal(await cart.locator(".cart-thumbnail").evaluate(node => node === document.activeElement), true);
    }
    await page.locator(".cart-drawer-close").click();
  });

  await t.test("negativos, cero y decimales: error sólo arriba; uno sigue válido", async () => {
    for (const panel of [false, true]) {
      await page.setViewportSize({ width: 1920, height: 1080 });
      let cart;
      if (panel) { await page.goto(base); await page.locator(".cart-link").click(); cart = page.frameLocator("#cart-drawer iframe"); }
      else { await page.goto(`${base}/carrito/`); cart = page; }
      await cart.locator("#cart-contents:not([aria-busy]) .cart-quantity").waitFor();
      for (const [value, message] of [["-2", "No se pueden ingresar valores negativos"], ["0", "Ingresá una cantidad de al menos 1."], ["3.3", "Solo se permiten cantidades enteras, sin decimales."]]) {
        await cart.locator(".cart-quantity").evaluate((node, value) => { node.value = value; }, value);
        await cart.locator(".cart-quantity").dispatchEvent("change");
        await cart.getByRole("alert").filter({ hasText: message }).waitFor();
        assert.equal(await cart.locator("[data-cart-error]:not([hidden]), .quantity-error:not([hidden])").count(), 0);
        assert.equal(await cart.locator(".cart-quantity").getAttribute("aria-invalid"), "true");
        assert.equal(await cart.locator("#cart-review").isDisabled(), true);
        assert.equal(await cart.locator("[data-quantity-error]").evaluate(node => getComputedStyle(node).clipPath), "inset(50%)");
        const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
        assert.deepEqual(axe.violations.map(v => v.id), []);
      }
      await cart.locator(".cart-quantity").fill("1");
      await cart.locator(".cart-quantity").dispatchEvent("change");
      await cart.locator("#cart-review:not([disabled])").waitFor();
      assert.equal(await cart.locator(".cart-quantity").inputValue(), "1");
      assert.equal(await cart.locator("[data-notification]:visible").count(), 0);
      if (panel) await page.locator(".cart-drawer-close").click();
    }
  });

  await t.test("formulario simple sin textarea, responsive y accesible", async () => {
    await page.goto(`${base}/carrito/`);
    await page.locator("#cart-review:not([disabled])").waitFor();
    for (const width of [1920, 390]) {
      await page.setViewportSize({ width, height: 1080 });
      await page.locator("#cart-review").click();
      await page.locator("#cart-review-dialog[open]").waitFor();
      assert.equal(await page.getByRole("button", { name: "Cancelar", exact: true }).count(), 1);
      assert.equal(await page.getByRole("button", { name: "Enviar", exact: true }).count(), 1);
      assert.equal(await page.locator("textarea, #copy-message").count(), 0);
      const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
      assert.deepEqual(axe.violations.map(v => v.id), []);
      await page.screenshot({ path: `.qa/screenshots/order-form-${width}.png` });
      await page.locator("#review-cancel").click();
      await page.locator("#cart-review:not([disabled])").waitFor();
    }
    assert.deepEqual(errors, []);
  });


});


test("Pesos enteros y cantidades sólo dígitos, sin avisos en el detalle", { timeout: 60000 }, async t => {
  const browser = await chromium.launch();
  t.after(() => browser.close());
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 }, permissions: ["clipboard-read", "clipboard-write"] });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(base);
  const card = page.locator(".add-product").first();
  await card.locator(".catalog-increase").click();
  const input = card.locator(".catalog-amount");

  async function rejectSymbols(field) {
    await field.fill("12");
    for (const key of [".", ",", "-", "+", "e", "a", " ", "/", "$"]) {
      await field.press("End"); await field.press(key);
      assert.equal(await field.inputValue(), "12", key);
    }
    for (const text of ["9,1", "9.1", "-2", "2e3", "1 2", "１２", "1\n2"]) {
      await page.evaluate(text => navigator.clipboard.writeText(text), text);
      await field.press("Control+V");
      assert.equal(await field.inputValue(), "12", `Pegado: ${text}`);
    }
    assert.equal(await field.evaluate(node => !node.dispatchEvent(new InputEvent("beforeinput", { bubbles: true, cancelable: true, inputType: "insertText", data: "," }))), true);
    await field.evaluate(node => { node.value = "9,1"; node.dispatchEvent(new Event("input", { bubbles: true })); });
    assert.equal(await field.inputValue(), "12");
    await field.press("Backspace");
    assert.equal(await field.inputValue(), "1");
  }

  await t.test("catálogo: caja editable, filtro por teclado/pegado/móvil y sincronización", async () => {
    assert.equal(await input.getAttribute("type"), "text");
    assert.equal(await input.getAttribute("inputmode"), "numeric");
    const box = await input.boundingBox(); assert.ok(box.width >= 44 && box.height >= 44);
    await rejectSymbols(input);
    await input.fill("3"); await input.press("Tab");
    await input.fill("5"); await card.locator(".catalog-increase").click();
    assert.equal(await input.inputValue(), "6");
    await page.locator(".cart-link").click();
    const cart = page.frameLocator("#cart-drawer iframe");
    await cart.locator("#cart-contents:not([aria-busy]) .total").waitFor();
    assert.equal(await cart.locator(".cart-quantity").inputValue(), "6");
    await page.locator(".cart-drawer-close").click();
  });

  await t.test("carrito directo y panel: sólo dígitos, mínimo 1 y error exclusivamente arriba", async () => {
    for (const panel of [false, true]) {
      let cart;
      if (panel) { await page.goto(base); await page.locator(".cart-link").click(); cart = page.frameLocator("#cart-drawer iframe"); }
      else { await page.goto(`${base}/carrito/`); cart = page; }
      await cart.locator("#cart-contents:not([aria-busy]) .cart-quantity").waitFor();
      const field = cart.locator(".cart-quantity");
      await rejectSymbols(field);
      await field.fill("0"); await field.dispatchEvent("change");
      await cart.getByRole("alert").filter({ hasText: /al menos 1/ }).waitFor();
      assert.equal(await cart.locator("#cart-review").isDisabled(), true);
      assert.equal(await cart.locator(".cart-item .notice:not([hidden])").count(), 0);
      await field.fill("1"); await field.dispatchEvent("change");
      await cart.locator("#cart-contents:not([aria-busy]) #cart-review:not([disabled])").waitFor();
      assert.equal(await cart.locator(".trash-icon:not([hidden])").count(), 1);
      assert.equal(await cart.locator(".cart-minus:not([hidden])").count(), 0);
      const text = await cart.locator("#cart-contents").innerText();
      assert.ok(!/\$ [0-9.]+,[0-9]{2}/.test(text), text);
      const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
      assert.deepEqual(axe.violations.map(v => v.id), []);
      await page.screenshot({ path: `.qa/screenshots/integer-quantities-${panel ? "panel" : "direct"}.png` });
      if (panel) await page.locator(".cart-drawer-close").click();
    }
  });

  await t.test("Admin: precios filtran símbolos y mantienen pesos enteros al guardar", async () => {
    await page.goto(`${base}/admin/login/`);
    await page.locator("#id_username").fill("qa-admin");
    await page.locator("#id_password").fill("qa-only-password-582");
    await page.locator('input[type="submit"]').click();
    await page.goto(`${base}/admin/catalog/product/add/`);
    for (const name of ["retail_price", "wholesale_price"]) {
      const field = page.locator(`#id_${name}`);
      await rejectSymbols(field);
      assert.equal(await field.getAttribute("pattern"), "[0-9]+");
    }
    assert.deepEqual(errors, []);
  });
});


test("WhatsApp: emojis íntegros en apertura directa y enlace de respaldo", { timeout: 60000 }, async t => {
  const browser = await chromium.launch();
  t.after(() => browser.close());
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(`${base}/admin/login/`);
  await page.locator("#id_username").fill("qa-admin");
  await page.locator("#id_password").fill("qa-only-password-582");
  await page.locator('input[type="submit"]').click();
  await page.goto(`${base}/admin/catalog/product/add/`);
  await page.locator("#id_category").selectOption({ index: 1 });
  await page.locator("#id_name").fill("QA Unicode 🛍️ 👩🏽‍🍳 🇦🇷");
  await page.locator("#id_description").fill("Caja de 5 kg.");
  await page.locator("#id_brand").fill("Marca 📌 & ñ + 50%");
  await page.locator("#id_sale_unit").selectOption("caja");
  await page.locator("#id_retail_price").fill("100");
  await page.locator('input[name="_save"]').click();
  await page.locator(".messagelist .success").waitFor();
  let destination = null;
  await context.route(/^https:\/\//, async route => {
    const url = new URL(route.request().url());
    assert.equal(url.hostname, "api.whatsapp.com", "No pasar por el acortador wa.me");
    assert.equal(url.pathname, "/send");
    destination = route.request().url();
    await route.fulfill({ contentType: "text/html; charset=utf-8", body: "<h1>WhatsApp interceptado sin enviar</h1>" });
  });
  await page.goto(`${base}/?q=QA%20Unicode`);
  await page.locator(".catalog-increase").first().click();
  await page.locator(".catalog-amount").first().fill("3");
  await page.locator(".catalog-amount").first().press("Tab");
  await page.evaluate(() => Notifications.close());

  for (const [panel, width] of [[false, 1920], [true, 390]]) {
    await t.test(`${panel ? "panel móvil" : "carrito desktop"}: botón y fallback conservan Unicode`, async () => {
      await page.setViewportSize({ width, height: 1080 });
      let cart;
      if (panel) { await page.goto(`${base}/?q=QA%20Unicode`); await page.locator(".catalog-increase").first().click(); await page.locator(".catalog-amount").first().fill("3"); await page.locator(".catalog-amount").first().press("Tab"); await page.evaluate(() => Notifications.close()); await page.locator(".cart-link").click(); cart = page.frameLocator("#cart-drawer iframe"); }
      else { await page.goto(`${base}/carrito/`); cart = page; }
      await cart.locator("#cart-contents:not([aria-busy]) #cart-review:not([disabled])").waitFor();
      await cart.locator("#cart-review").click();
      await cart.locator("#id_full_name").waitFor();
      await cart.locator("#id_full_name").fill("Ana Unicode QA");
      const opening = context.waitForEvent("page");
      await cart.locator("#review-continue").click();
      const popup = await opening;
      await popup.getByRole("heading", { name: "WhatsApp interceptado sin enviar" }).waitFor({ timeout: 5000 });
      const original = new URL(destination).searchParams.get("text");
      assert.ok(original.includes("🛍️") && original.includes("👩🏽‍🍳") && original.includes("🇦🇷") && original.includes("📌"));
      assert.ok(!original.includes("�"));
      assert.ok(original.includes("*1. QA Unicode 🛍️ 👩🏽‍🍳 🇦🇷*"));
      assert.ok(original.includes("Cantidad: 3 cajas de 5 kg"));
      assert.ok(original.includes("Precio: $ 100 por caja"));
      assert.ok(original.includes("*Subtotal: $ 300*"));
      assert.ok(!original.includes("minorista") && !original.includes("mayorista"));
      assert.ok(destination.includes("%F0%9F%9B%8D%EF%B8%8F"));
      assert.ok(!destination.includes("%EF%BF%BD") && !destination.includes("%25F0"));
      assert.equal(await popup.evaluate(() => window.opener), null);
      await popup.close();
      await page.locator("#order-result-dialog[open]").waitFor();
      const ready = new URL(await page.locator("#whatsapp-ready").getAttribute("href"));
      assert.equal(ready.searchParams.get("text"), original);
      const manualOpening = context.waitForEvent("page");
      await page.locator("#whatsapp-ready").click();
      const manual = await manualOpening;
      await manual.getByRole("heading", { name: "WhatsApp interceptado sin enviar" }).waitFor({ timeout: 5000 });
      assert.equal(new URL(destination).searchParams.get("text"), original);
      await manual.close();
      if (panel) await page.locator("#order-result-close").click();
    });
  }
  assert.deepEqual(errors, []);
});

require("./orders.browser.cjs");

require("./mobile.browser.cjs");
