(function (root) {
  "use strict";
  const STORAGE_KEY = "dulce-salado.cart.v1";
  function hundredths(value) {
    const text = String(value).replace(",", ".");
    if (!/^\d{1,7}(\.\d{1,2})?$/.test(text)) throw new Error("Ingresá una cantidad con hasta dos decimales.");
    const [whole, fraction = ""] = text.split(".");
    return Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
  }
  function quantityText(value) {
    return `${Math.floor(value / 100)}.${String(value % 100).padStart(2, "0")}`;
  }
  function selection(item) {
    if (!item || !Number.isSafeInteger(item.id) || item.id <= 0 || typeof item.quantity !== "string" || item.quantity.length > 20 || !["retail", "wholesale"].includes(item.price_type)) throw new Error("El carrito guardado tiene datos inválidos. Vaciá el carrito para restablecerlo.");
    return { id: item.id, quantity: item.quantity, price_type: item.price_type, revision: typeof item.revision === "string" ? item.revision : "", sale_unit: typeof item.sale_unit === "string" ? item.sale_unit : "" };
  }
  function read(storage) {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const data = JSON.parse(raw);
    if (data.version !== 1 || !Array.isArray(data.items)) throw new Error("El carrito guardado tiene un formato inválido. Vaciá el carrito para restablecerlo.");
    const items = data.items.map(selection);
    if (new Set(items.map(item => item.id)).size !== items.length) throw new Error("El carrito guardado contiene productos repetidos. Vaciá el carrito para restablecerlo.");
    return items;
  }
  function write(storage, items) {
    storage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, items: items.map(selection) }));
  }
  function add(items, item, step) {
    const amount = hundredths(item.quantity), increment = hundredths(step);
    if (amount <= 0 || increment <= 0 || amount % increment !== 0) throw new Error(`La cantidad debe ser positiva y múltiplo de ${step} ${item.sale_unit}.`);
    const existing = items.find(entry => entry.id === item.id);
    if (existing && (existing.price_type !== item.price_type || existing.sale_unit !== item.sale_unit)) throw new Error("Este producto ya está en el carrito con otra selección. Revisalo desde el carrito.");
    const sum = amount + (existing ? hundredths(existing.quantity) : 0);
    if (sum > 999999999) throw new Error("La cantidad supera el máximo permitido.");
    const result = items.filter(entry => entry.id !== item.id);
    result.push(selection({ ...item, quantity: quantityText(sum) }));
    return result;
  }
  const api = { STORAGE_KEY, hundredths, quantityText, read, write, add };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.CartCore = api;
})(typeof window === "undefined" ? globalThis : window);
