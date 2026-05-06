let lastResponse = null;
let activeTab = "config";

const promptEl = document.querySelector("#prompt");
const outputEl = document.querySelector("#output");
const metricsEl = document.querySelector("#metrics");
const compileBtn = document.querySelector("#compile");

function render() {
  if (!lastResponse) return;
  const payload = {
    config: lastResponse.compiled_config,
    validation: {
      before_repair: lastResponse.validation_before_repair,
      after_repair: lastResponse.validation_after_repair,
    },
    runtime: lastResponse.runtime,
  }[activeTab];
  outputEl.textContent = JSON.stringify(payload, null, 2);
  metricsEl.innerHTML = `
    <span>Latency: ${lastResponse.metrics.latency_ms}ms</span>
    <span>Repair iterations: ${lastResponse.metrics.repair_iterations}</span>
    <span>Executable: ${lastResponse.runtime.executable}</span>
  `;
}

compileBtn.addEventListener("click", async () => {
  compileBtn.disabled = true;
  compileBtn.textContent = "Compiling...";
  try {
    const response = await fetch("/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: promptEl.value }),
    });
    lastResponse = await response.json();
    render();
  } finally {
    compileBtn.disabled = false;
    compileBtn.textContent = "Compile";
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

compileBtn.click();
