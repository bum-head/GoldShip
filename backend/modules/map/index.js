// Map module: placeholder. The original map.js was empty, so this only proves the slot works.
// Add your map logic here (geocoding, field boundaries, distances...).
module.exports = {
  name: "map",
  description: "Placeholder for map features (not implemented yet)",
  version: "0.1.0",

  routes: [
    {
      method: "GET",
      path: "/status",
      description: "Placeholder route",
      handler: async () => ({ message: "map module is loaded but has no features yet" }),
    },
  ],

  health: async () => ({ ok: true, detail: "placeholder module" }),
};
