# GoldShip backend

Modular Node.js backend (no dependencies, Node 18+).

    node server.js        # then open http://localhost:8080  (dashboard)

## Layout

    server.js          entry point
    core/              loader, router, health checks, static files (rarely touched)
    modules/           one folder per feature, auto-loaded
      climate/         weather data + Good→Bad rating
      map/             placeholder
      _template/       copy me (folders starting with _ are ignored)
    public/            dashboard

## Adding a module

1. Copy `modules/_template` to `modules/<yourname>`
2. Edit `index.js` (name, routes, optional `health` and `init`)
3. Restart the server. Routes appear at `/api/<name>/...` and on the dashboard.

A module that throws or breaks the contract is shown as **failed** on the dashboard;
the rest of the backend keeps running.

## Core endpoints

| Endpoint | What it returns |
|---|---|
| `GET /api/modules` | loaded modules and their routes |
| `GET /api/health`  | health check result for every module |

## Settings (environment variables)

`PORT` (8080) · `CORS_ORIGINS` (Django site origins) · `WEATHER_API_URL`
