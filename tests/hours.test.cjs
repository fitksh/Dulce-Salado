const test = require("node:test");
const assert = require("node:assert/strict");
const { currentStatus } = require("../static/js/business-hours.js");
const data = { initialized: true, intervals: [
  { day: 0, opens: "09:00:00", closes: "12:00:00" },
  { day: 0, opens: "15:00:00", closes: "18:00:00" }
] };
test("uninitialized hours stay unknown; a published empty week is closed", () => {
  assert.equal(currentStatus({ ...data, initialized: false }).label, "Horarios no disponibles");
  assert.equal(currentStatus({ initialized: true, intervals: [] }).label, "Cerrado");
});
test("Buenos Aires clock supports split hours, exact boundaries and closed days", () => {
  for (const [date, opened] of [
    ["2026-10-12T08:59:59-03:00", false], ["2026-10-12T09:00:00-03:00", true],
    ["2026-10-12T11:59:59-03:00", true], ["2026-10-12T12:00:00-03:00", false],
    ["2026-10-12T14:59:59-03:00", false], ["2026-10-12T15:00:00-03:00", true],
    ["2026-10-12T18:00:00-03:00", false], ["2026-10-13T10:00:00-03:00", false],
    ["2026-10-12T12:00:00Z", true], ["2026-10-13T01:00:00Z", false]
  ]) assert.equal(currentStatus(data, new Date(date)).open, opened, date);
});
