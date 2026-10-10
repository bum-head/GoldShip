const fs = require("fs");
const path = require("path");

const PUBLIC_DIR = path.join(__dirname, "..", "public");
const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon",
};

// Serves a file from /public. Returns false if there is no such file.
function serveStatic(pathname, res) {
  let requested;
  try { requested = decodeURIComponent(pathname === "/" ? "/index.html" : pathname); } catch { return false; }
  const file = path.normalize(path.join(PUBLIC_DIR, requested));

  if (!file.startsWith(PUBLIC_DIR + path.sep)) return false;           // block ../ tricks
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) return false;

  res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
  return true;
}

module.exports = { serveStatic };
