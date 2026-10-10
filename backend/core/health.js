const config = require("./config");

function withTimeout(promise, ms) {
  let timer;
  const timeout = new Promise((_, reject) => { timer = setTimeout(() => reject(new Error(`timed out after ${ms} ms`)), ms); });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

async function checkModule(m) {
  if (m.status === "failed") return { name: m.name, status: "failed", detail: m.error, latencyMs: 0 };

  const start = Date.now();
  try {
    const result = m.health ? await withTimeout(Promise.resolve(m.health()), config.HEALTH_TIMEOUT_MS) : { ok: true, detail: "no health check defined" };
    return { name: m.name, status: result.ok ? "ok" : "down", detail: result.detail || "", latencyMs: Date.now() - start };
  } catch (e) {
    return { name: m.name, status: "down", detail: e.message, latencyMs: Date.now() - start };
  }
}

// Runs every module's health check in parallel.
async function runHealth(modules, startedAt) {
  const checks = await Promise.all(modules.map(checkModule));
  return {
    status: checks.every((c) => c.status === "ok") ? "ok" : "degraded",
    time: new Date().toISOString(),
    uptimeSec: Math.round((Date.now() - startedAt) / 1000),
    node: process.version,
    port: config.PORT,
    modules: checks,
  };
}

module.exports = { runHealth };
