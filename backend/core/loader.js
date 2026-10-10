// Finds every folder in /modules, loads it, and checks it follows the module contract.
// A broken module is recorded as "failed" instead of crashing the server.
const fs = require("fs");
const path = require("path");

const NAME_RE = /^[a-z][a-z0-9-]*$/;
const METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"];

function validate(mod) {
  if (!mod || typeof mod !== "object") throw new Error("module must export an object");
  if (!NAME_RE.test(mod.name || "")) throw new Error('"name" must be lowercase letters, digits or dashes');
  if (mod.health !== undefined && typeof mod.health !== "function") throw new Error('"health" must be a function');
  if (mod.init !== undefined && typeof mod.init !== "function") throw new Error('"init" must be a function');
  for (const r of mod.routes || []) {
    if (!METHODS.includes(r.method)) throw new Error(`route method must be one of ${METHODS.join(", ")}`);
    if (typeof r.path !== "string" || !r.path.startsWith("/")) throw new Error(`route path "${r.path}" must start with "/"`);
    if (typeof r.handler !== "function") throw new Error(`route ${r.method} ${r.path} needs a handler function`);
  }
}

async function loadModules(dir) {
  const registry = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true })
    .filter((e) => e.isDirectory() && !e.name.startsWith("_") && !e.name.startsWith("."))
    .sort((a, b) => a.name.localeCompare(b.name));

  for (const entry of entries) {
    try {
      const mod = require(path.join(dir, entry.name));
      validate(mod);
      if (registry.some((m) => m.name === mod.name)) throw new Error(`duplicate module name "${mod.name}"`);
      if (mod.init) await mod.init();
      registry.push({
        name: mod.name,
        description: mod.description || "",
        version: mod.version || "0.0.0",
        status: "loaded",
        routes: mod.routes || [],
        health: mod.health,
      });
      console.log(`  ✔ module loaded: ${mod.name}`);
    } catch (e) {
      registry.push({ name: entry.name, description: "", version: "", status: "failed", error: e.message, routes: [] });
      console.error(`  ✘ module failed: ${entry.name} — ${e.message}`);
    }
  }
  return registry;
}

module.exports = { loadModules };
