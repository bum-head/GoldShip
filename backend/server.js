// Backend entry point.  Run:  node server.js   (Node 18+)   then open http://localhost:8080
const http = require("http");
const config = require("./core/config");
const { createApp } = require("./core/app");

createApp().then((handle) => {
  http.createServer(handle).listen(config.PORT, () => {
    console.log(`Backend running at http://localhost:${config.PORT}  (dashboard at /)`);
  });
});
