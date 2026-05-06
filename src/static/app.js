let lastResponse = null;
let activeTab = "overview";

const promptEl = document.querySelector("#prompt");
const outputEl = document.querySelector("#output");
const overviewEl = document.querySelector("#overview");
const compileBtn = document.querySelector("#compile");
const copyBtn = document.querySelector("#copyJson");
const latencyMetric = document.querySelector("#latencyMetric");
const repairMetric = document.querySelector("#repairMetric");
const runtimeMetric = document.querySelector("#runtimeMetric");
const validationState = document.querySelector("#validationState");
const validationDetail = document.querySelector("#validationDetail");
const runtimeState = document.querySelector("#runtimeState");
const runtimeDetail = document.querySelector("#runtimeDetail");
const surfaceState = document.querySelector("#surfaceState");
const surfaceDetail = document.querySelector("#surfaceDetail");

function render() {
  if (!lastResponse) return;
  const payload = {
    overview: buildOverviewPayload(),
    config: lastResponse.compiled_config,
    validation: {
      before_repair: lastResponse.validation_before_repair,
      after_repair: lastResponse.validation_after_repair,
    },
    runtime: lastResponse.runtime,
  }[activeTab];

  updateSummary();
  if (activeTab === "overview") {
    outputEl.hidden = true;
    overviewEl.hidden = false;
    overviewEl.innerHTML = renderOverview();
    return;
  }

  overviewEl.hidden = true;
  outputEl.hidden = false;
  outputEl.textContent = JSON.stringify(payload, null, 2);
}

compileBtn.addEventListener("click", async () => {
  compileBtn.disabled = true;
  compileBtn.textContent = "Compiling";
  try {
    const response = await fetch("/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: promptEl.value }),
    });
    lastResponse = await response.json();
    render();
  } catch (error) {
    outputEl.hidden = false;
    overviewEl.hidden = true;
    outputEl.textContent = JSON.stringify({ error: "Compile request failed", detail: String(error) }, null, 2);
  } finally {
    compileBtn.disabled = false;
    compileBtn.textContent = "Compile app";
  }
});

document.querySelectorAll("[data-tab]").forEach((button) => {
  button.addEventListener("click", () => {
    activeTab = button.dataset.tab;
    document.querySelectorAll("[data-tab]").forEach((tab) => tab.classList.remove("active"));
    button.classList.add("active");
    render();
  });
});

copyBtn.addEventListener("click", async () => {
  if (!lastResponse) return;
  await navigator.clipboard.writeText(JSON.stringify(lastResponse.compiled_config, null, 2));
  copyBtn.textContent = "Copied";
  setTimeout(() => {
    copyBtn.textContent = "Copy JSON";
  }, 1400);
});

function updateSummary() {
  const metrics = lastResponse.metrics;
  const validation = lastResponse.validation_after_repair;
  const runtime = lastResponse.runtime;
  const pageCount = lastResponse.compiled_config.ui.pages.length;
  const endpointCount = lastResponse.compiled_config.api.endpoints.length;

  latencyMetric.textContent = `${metrics.latency_ms}ms`;
  repairMetric.textContent = String(metrics.repair_iterations);
  runtimeMetric.textContent = runtime.executable ? "Pass" : "Fail";

  validationState.textContent = validation.ok ? "Schema clean" : "Needs attention";
  validationDetail.textContent = `${metrics.issue_count_before_repair} issue(s) before repair, ${metrics.issue_count_after_repair} after`;
  runtimeState.textContent = runtime.executable ? "Executable" : "Blocked";
  runtimeDetail.textContent = `${runtime.smoke_tests.length} smoke check(s), ${runtime.mounted_endpoints.length} route(s) mounted`;
  surfaceState.textContent = `${pageCount} / ${endpointCount}`;
  surfaceDetail.textContent = "Pages / API endpoints";
}

function buildOverviewPayload() {
  const config = lastResponse.compiled_config;
  return {
    app_name: config.app_name,
    pages: config.ui.pages.map((page) => page.path),
    endpoints: config.api.endpoints.map((endpoint) => `${endpoint.method} ${endpoint.path}`),
    tables: config.database.tables.map((table) => table.name),
    business_rules: config.business_logic.map((rule) => rule.id),
  };
}

function renderOverview() {
  const config = lastResponse.compiled_config;
  const validation = lastResponse.validation_after_repair;
  const runtime = lastResponse.runtime;
  return `
    <div class="overview-grid">
      ${renderList("Pages", config.ui.pages.map((page) => page.path))}
      ${renderList("API Endpoints", config.api.endpoints.map((endpoint) => `${endpoint.method} ${endpoint.path}`))}
      ${renderList("Database Tables", config.database.tables.map((table) => table.name))}
      ${renderList("Business Rules", config.business_logic.length ? config.business_logic.map((rule) => rule.id) : ["No premium or custom rule required"])}
    </div>
    <div class="proof-row">
      <div>
        <span class="summary-label">Validation proof</span>
        <strong>${validation.ok ? "All cross-layer checks passed" : "Issues found"}</strong>
        <small>${validation.issues.length} remaining issue(s)</small>
      </div>
      <div>
        <span class="summary-label">Execution proof</span>
        <strong>${runtime.executable ? "Runtime simulator passed" : "Runtime simulator failed"}</strong>
        <small>${runtime.smoke_tests.slice(0, 3).join(", ")}${runtime.smoke_tests.length > 3 ? "..." : ""}</small>
      </div>
    </div>
  `;
}

function renderList(title, items) {
  return `
    <article class="overview-card">
      <h2>${title}</h2>
      <ul>
        ${items.map((item) => `<li>${item}</li>`).join("")}
      </ul>
    </article>
  `;
}

compileBtn.click();
