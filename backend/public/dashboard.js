const $ = (id) => document.getElementById(id);
const REFRESH_MS = 5000;
let timer = null;

// Small DOM helper. Uses textContent only, so server text can never inject markup.
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function getJson(url) {
  const start = performance.now();
  const res = await fetch(url, { cache: "no-store" });
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  return { status: res.status, ok: res.ok, ms: Math.round(performance.now() - start), data };
}

function setOverall(state, text) {
  const pill = $("overall");
  pill.dataset.s = state;
  pill.textContent = text;
}

function renderSystem(h) {
  const items = [
    ["Uptime", formatUptime(h.uptimeSec)],
    ["Port", h.port],
    ["Node", h.node],
    ["Modules", `${h.modules.filter((m) => m.status === "ok").length} / ${h.modules.length} healthy`],
  ];
  $("system").replaceChildren(...items.map(([label, value]) => {
    const box = el("div", "stat");
    box.append(el("small", "", label), el("span", "", String(value)));
    return box;
  }));
}

function formatUptime(s) {
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${s % 60}s`;
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
}

function renderModules(mods, checks) {
  const byName = Object.fromEntries(checks.map((c) => [c.name, c]));
  if (!mods.length) {
    $("modules").replaceChildren(el("p", "desc", "No modules found. Add a folder to modules/."));
    return;
  }

  $("modules").replaceChildren(...mods.map((m) => {
    const check = byName[m.name] || { status: "down", detail: "no health result", latencyMs: 0 };
    const card = el("div", "module");
    card.dataset.s = check.status;

    const head = el("div", "module-head");
    const pill = el("span", "pill", check.status);
    pill.dataset.s = check.status;
    head.append(el("strong", "", m.name), pill);
    if (m.version) head.append(el("span", "version", `v${m.version}`));
    if (m.status === "loaded") head.append(el("span", "latency", `${check.latencyMs} ms`));
    card.append(head);

    if (m.description) card.append(el("p", "desc", m.description));
    if (check.detail) card.append(el("p", check.status === "ok" ? "detail" : "detail err", check.detail));

    if (m.routes.length) {
      const list = el("ul", "routes");
      for (const r of m.routes) {
        const li = el("li");
        li.append(el("span", "method", r.method), el("span", "path", r.path));
        if (r.description) li.append(el("span", "note", r.description));
        if (r.method === "GET") {
          const btn = el("button", "", "Call");
          btn.addEventListener("click", () => callRoute(r.path));
          li.append(btn);
        }
        list.append(li);
      }
      card.append(list);
    }
    return card;
  }));
}

async function callRoute(path) {
  $("resMeta").textContent = `GET ${path} …`;
  $("resBody").textContent = "";
  try {
    const r = await getJson(path);
    $("resMeta").textContent = `GET ${path} → ${r.status} in ${r.ms} ms`;
    $("resBody").textContent = typeof r.data === "string" ? r.data : JSON.stringify(r.data, null, 2);
  } catch (e) {
    $("resMeta").textContent = `GET ${path} failed: ${e.message}`;
  }
}

async function refresh() {
  try {
    const [mods, health] = await Promise.all([getJson("/api/modules"), getJson("/api/health")]);
    if (!mods.ok || !health.ok) throw new Error(`HTTP ${mods.ok ? health.status : mods.status}`);
    setOverall(health.data.status, health.data.status === "ok" ? "all systems ok" : "degraded");
    renderSystem(health.data);
    renderModules(mods.data, health.data.modules);
    $("updated").textContent = `Updated ${new Date().toLocaleTimeString()}`;
  } catch (e) {
    setOverall("unreachable", "backend unreachable");
    $("updated").textContent = e.message;
  }
}

function schedule() {
  clearInterval(timer);
  if ($("auto").checked) timer = setInterval(refresh, REFRESH_MS);
}

$("refresh").addEventListener("click", refresh);
$("auto").addEventListener("change", schedule);
refresh();
schedule();
