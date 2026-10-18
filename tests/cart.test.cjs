const test = require("node:test");
const assert = require("node:assert/strict");
const cart = require("../static/js/cart-core.js");
const item = { id: 1, quantity: "1.00", price_type: "retail", sale_unit: "kg", revision: "test" };

test("quantities add exactly and only accept integer presentations", () => {
  assert.equal(cart.add([item], item)[0].quantity, "2.00");
  for (const quantity of ["0.15", "0", "NaN", "1.5"]) assert.throws(() => cart.add([], { ...item, quantity }));
  assert.throws(() => cart.add([], item, "0.1"));
  assert.throws(() => cart.add([{ ...item, quantity: "0.1" }], item));
});
test("adding another price type requires explicit cart review", () => {
  assert.throws(() => cart.add([item], { ...item, price_type: "wholesale" }));
});
test("stepper uses one, a minimum and rejects old fractional increments", () => {
  assert.equal(cart.adjustQuantity("2.00", "1", 1), "3.00");
  assert.equal(cart.adjustQuantity("3,00", "1", -1), "2.00");
  assert.equal(cart.adjustQuantity("1", "1", -1), "1.00");
  for (const value of ["", "0", "0.15", "-1", "NaN"]) assert.throws(() => cart.adjustQuantity(value, "1", 1));
  assert.throws(() => cart.adjustQuantity("2", "2", 1));
  assert.throws(() => cart.adjustQuantity("9999999", "1", 1));
});
test("catalog plus starts retail at one, keeps order and normalizes legacy wholesale", () => {
  const first = cart.changeProduct([], item, 1);
  assert.equal(first[0].quantity, "1.00");
  const wholesale = [{ ...first[0], price_type: "wholesale", revision: "old" }, { ...item, id: 2 }];
  const next = cart.changeProduct(wholesale, { ...item, revision: "new" }, 1);
  assert.equal(next[0].quantity, "2.00");
  assert.equal(next[0].price_type, "retail");
  assert.equal(next[0].revision, "old");
  assert.deepEqual(next.map(entry => entry.id), [1, 2]);
});
test("catalog minus reaches one, then trash removes only that presentation", () => {
  const two = [{ ...item, quantity: "2.00" }, { ...item, id: 2 }];
  const one = cart.changeProduct(two, item, -1);
  assert.equal(one[0].quantity, "1.00");
  assert.deepEqual(cart.changeProduct(one, item, -1).map(entry => entry.id), [2]);
  assert.throws(() => cart.changeProduct([{ ...item, quantity: "0.3" }], item, 1));
  assert.throws(() => cart.changeProduct([item], { ...item, sale_unit: "100 gr" }, 1));
});
test("storage survives reload and drops all prices; legacy quantities remain reviewable", () => {
  let stored;
  const storage = { setItem: (key, value) => { stored = value; }, getItem: () => stored };
  cart.write(storage, [{ ...item, price: "999", subtotal: "999", name: "test" }]);
  assert.deepEqual(cart.read(storage), [item]);
  assert.equal(stored.includes("999"), false);
  const old = { ...item, quantity: "0.3" };
  cart.write(storage, [old]);
  assert.deepEqual(cart.read(storage), [old]);
});
test("corrupt storage and duplicate IDs are rejected without clearing it", () => {
  for (const value of ["invalid", "null", "{}", JSON.stringify({ version: 1, items: [item, item] }), JSON.stringify({ version: 1, items: [{ ...item, id: -1 }] })]) {
    assert.throws(() => cart.read({ getItem: () => value }), { name: "CartDataError" });
  }
  const blocked = new DOMException("Blocked", "SecurityError");
  assert.throws(() => cart.read({ getItem() { throw blocked; } }), error => error === blocked);
});
