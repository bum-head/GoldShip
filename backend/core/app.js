// Builds the request handler: core routes + every loaded module's routes under /api/<module>/...
const path = require("path");
const config = require("./config");
const { HttpError } = require("./errors");
const { loadModules } = require("./loader");
const { runHealth } = require("./health");
const { serveStatic } = require("./static");

const MODULES_DIR = path.join(__dirname, "..", "modules");
const MAX_BODY = 1024 * 1024; // 1 MB

function sendJson(res, status, body) {
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
  res.end(JSON.stringify(body));
}

// Helper handed to handlers so POST modules can read a JSON body.
function readJson(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on("data", (c) => {
      size += c.length;
      if (size > MAX_BODY) { reject(new HttpError(413, "Body too large")); req.destroy(); return; }
      chunks.push(c);
    });
    req.on("end", () => {
      if (!chunks.length) return resolve({});
      try { resolve(JSON.parse(Buffer.concat(chunks).toString())); }
      catch { reject(new HttpError(400, "Body is not valid JSON")); }
    });
    req.on("error", reject);
  });
}

async function createApp() {
  const startedAt = Date.now();
  console.log("Loading modules:");
  const modules = await loadModules(MODULES_DIR);

  const routes = new Map(); // "GET /api/climate/rating" -> handler
  const add = (method, p, handler) => routes.set(`${method} ${p}`, handler);

  // Core routes
  add("GET", "/api/modules", () => modules.map((m) => ({
    name: m.name, description: m.description, version: m.version, status: m.status, error: m.error,
    routes: m.routes.map((r) => ({ method: r.method, path: `/api/${m.name}${r.path}`, description: r.description || "" })),
  })));
  add("GET", "/api/health", () => runHealth(modules, startedAt));

  // Module routes
  for (const m of modules.filter((m) => m.status === "loaded")) {
    for (const r of m.routes) add(r.method, `/api/${m.name}${r.path}`, r.handler);
  }


  return async function handle(req, res) {
    const origin = req.headers.origin;
    const allowedOrigin = origin && config.CORS_ORIGINS.includes(origin);

    if (allowedOrigin) {
      res.setHeader("Access-Control-Allow-Origin", origin);
      res.setHeader("Vary", "Origin");
    }

    const url = new URL(req.url, "http://localhost");
    const pathname = url.pathname.length > 1
      ? url.pathname.replace(/\/+$/, "")
      : url.pathname;

    try {
      if (pathname.startsWith("/api/")) {
        // Handle browser CORS preflight requests before route lookup.
        if (req.method === "OPTIONS") {
          if (!allowedOrigin) {
            return sendJson(res, 403, { error: "Origin not allowed" });
          }

          res.writeHead(204, {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "600",
            "Vary": "Origin",
          });
          return res.end();
        }

        const handler = routes.get(`${req.method} ${pathname}`);

        if (handler) {
          const data = await handler({
            req,
            res,
            url,
            query: Object.fromEntries(url.searchParams),
            json: () => readJson(req),
          });

          return sendJson(res, 200, data === undefined ? { ok: true } : data);
        }

        const otherMethod = [...routes.keys()].some(
          (k) => k.endsWith(` ${pathname}`)
        );

        return sendJson(
          res,
          otherMethod ? 405 : 404,
          { error: otherMethod ? "Method not allowed" : "Not found" }
        );
      }

      if (req.method === "GET" && serveStatic(pathname, res)) return;

      sendJson(
        res,
        req.method === "GET" ? 404 : 405,
        { error: req.method === "GET" ? "Not found" : "Method not allowed" }
      );
    } catch (e) {
      if (e instanceof HttpError) {
        return sendJson(res, e.status, { error: e.message });
      }

      console.error(e);
      sendJson(res, 500, { error: "Internal server error" });
    }
  };
}


module.exports = { createApp };
