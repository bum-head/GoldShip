// MODULE TEMPLATE
// To add a module: copy this folder, rename it (no leading underscore), restart the server.
// It is picked up automatically and appears on the dashboard. Folders starting with "_" are ignored.
const { HttpError } = require("../../core/errors");

module.exports = {
  // Required. Lowercase letters/digits/dashes. Routes are mounted at /api/<name>/...
  name: "example",

  // Optional. Shown on the dashboard.
  description: "What this module does",
  version: "1.0.0",

  // Optional. Runs once at startup. Throw to mark the module as failed (server keeps running).
  init: async () => {},

  // Optional. Return { ok: true|false, detail: "text" }. The dashboard calls it every few seconds.
  health: async () => ({ ok: true, detail: "all good" }),

  routes: [
    {
      method: "GET",
      path: "/hello",                       // -> GET /api/example/hello?name=Ada
      description: "Says hello",
      handler: async ({ query }) => ({ message: `Hello ${query.name || "world"}` }),
    },
    {
      method: "POST",
      path: "/echo",                        // -> POST /api/example/echo  with a JSON body
      description: "Echoes the JSON body",
      handler: async ({ json }) => {
        const body = await json();
        if (!body.text) throw new HttpError(400, '"text" is required');
        return { echoed: body.text };
      },
    },
  ],
};
