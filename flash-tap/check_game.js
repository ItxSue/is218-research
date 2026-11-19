// Check the browser state transitions with a deterministic timer and clock.
const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const html = fs.readFileSync(__dirname + "/templates/game.html", "utf8");
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const listeners = {};
const elements = {};
for (const id of ["round", "status", "milliseconds", "save"]) {
    elements[id] = {
        textContent: "",
        hidden: true,
        classList: { add() {} },
        focus() {},
        addEventListener(type, callback) { listeners[type] = callback; },
        click() { listeners.click(); },
    };
}
let callback;
let now = 100;
let cancelled = false;
vm.runInNewContext(script, {
    document: { getElementById(id) { return elements[id]; } },
    performance: { now() { return now; } },
    setTimeout(fn) { callback = fn; return 1; },
    clearTimeout() { cancelled = true; },
    Math,
});
const press = () => listeners.keydown({ key: "Enter", repeat: false, preventDefault() {} });
press();
assert.equal(elements.round.textContent, "Wait…");
press();
assert.equal(cancelled, true);
assert.match(elements.status.textContent, /Too soon/);
press();
callback();
assert.equal(elements.round.textContent, "TAP NOW");
now = 345;
press();
assert.equal(elements.milliseconds.value, 245);
assert.equal(elements.save.hidden, false);
console.log("PASS — keyboard start, false start, ready cue, elapsed timing and save visibility");
