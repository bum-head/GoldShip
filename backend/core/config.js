module.exports = {
  PORT: Number(process.env.PORT) || 8080,
  // Sites allowed to call the API from a browser (your Django site)
  CORS_ORIGINS: (process.env.CORS_ORIGINS || "http://localhost:8000,http://127.0.0.1:8000")
    .split(/[\s,]+/).filter(Boolean),
  HEALTH_TIMEOUT_MS: 3000,
};
