const test = require("node:test");
const assert = require("node:assert/strict");
const cart = require("../static/js/cart-core.js");
const item = { id: 1, quantity: "0.1", price_type: "retail", sale_unit: "kg", revision: "test" };

test("quantities add exactly and respect increments", () => {
  assert.equal(cart.add([item], item, "0.1")[0].quantity, "0.20");
  assert.throws(() => cart.add([], { ...item, quantity: "0.15" }, "0.1"));
  assert.throws(() => cart.add([], { ...item, quantity: "0" }, "0.1"));
  assert.throws(() => cart.hundredths("NaN"));
});
test("adding another price type requires explicit cart review", () => {
  assert.throws(() => cart.add([item], { ...item, price_type: "wholesale" }, "0.1"));
});
test("stepper uses exact increments, a minimum and clear invalid input errors", () => {
  assert.equal(cart.adjustQuantity("0.20", "0.10", 1), "0.30");
  assert.equal(cart.adjustQuantity("0,30", "0.10", -1), "0.20");
  assert.equal(cart.adjustQuantity("0.10", "0.10", -1), "0.10");
  assert.equal(cart.adjustQuantity("2", "2", 1), "4.00");
  for (const value of ["", "0", "0.15", "-1", "NaN"]) assert.throws(() => cart.adjustQuantity(value, "0.10", 1));
  assert.throws(() => cart.adjustQuantity("9999999.99", "0.01", 1));
});
test("storage survives reload and drops all prices", () => {
  let stored;
  const storage = { setItem: (key, value) => { stored = value; }, getItem: () => stored };
  cart.write(storage, [{ ...item, price: "999", subtotal: "999", name: "test" }]);
  assert.deepEqual(cart.read(storage), [item]);
  assert.equal(stored.includes("999"), false);
});
test("corrupt storage and duplicate IDs are rejected without clearing it", () => {
  assert.throws(() => cart.read({ getItem: () => "invalid" }));
  assert.throws(() => cart.read({ getItem: () => JSON.stringify({ version: 1, items: [item, item] }) }));
});
