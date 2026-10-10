(function (root) {
  "use strict";
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Argentina/Buenos_Aires", weekday: "short",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23"
  });
  function seconds(value) {
    const [hour, minute, second = 0] = value.split(":").map(Number);
    return hour * 3600 + minute * 60 + second;
  }
  function currentStatus(data, date = new Date()) {
    if (!data.initialized) return { open: false, label: "Horarios no disponibles" };
    const parts = Object.fromEntries(formatter.formatToParts(date).map(part => [part.type, part.value]));
    const day = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].indexOf(parts.weekday);
    const time = seconds(`${parts.hour}:${parts.minute}:${parts.second}`);
    const open = data.intervals.some(interval => interval.day === day && seconds(interval.opens) <= time && time < seconds(interval.closes));
    return { open, label: open ? "Abierto" : "Cerrado" };
  }
  if (typeof module !== "undefined" && module.exports) { module.exports = { currentStatus }; return; }
  const source = root.document.getElementById("business-hours-data");
  if (!source) return;
  const data = JSON.parse(source.textContent);
  function update() {
    const status = currentStatus(data);
    root.document.getElementById("business-status-text").textContent = status.label;
    root.document.getElementById("business-status-dot").classList.toggle("open", status.open);
  }
  update();
  root.setInterval(update, 15000);
  root.document.addEventListener("visibilitychange", () => { if (root.document.visibilityState === "visible") update(); });
})(typeof window === "undefined" ? globalThis : window);
