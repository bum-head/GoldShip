const http = require("http");
const fs = require("fs");

http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost:8080");

  // Serve the HTML page
  if (url.pathname === "/") {
    res.writeHead(200, { "Content-Type": "text/html" });
    return res.end(fs.readFileSync("index.html"));
  }

  // Return raw weather JSON
  if (url.pathname === "/weather"|| url.pathname === "/climate.html") {
    const lat = url.searchParams.get("lat") || "26.73";
    const lon = url.searchParams.get("lon") || "93.15";
    const api = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`;
    try {
      const data = await (await fetch(api)).text();
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(data);
    } catch (e) {
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: e.message }));
    }
    return;
  }

  res.writeHead(404);
  res.end();
}).listen(8080, () => console.log("Open http://localhost:8080"));