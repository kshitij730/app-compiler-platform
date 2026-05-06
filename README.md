# App Compiler Platform

Natural language -> structured config -> validated -> repaired -> executable app simulation.

This project is built for the AI Platform Engineer demo task. It treats app generation like a compiler pipeline rather than a single prompt:

1. **Intent Extraction** parses product language into a typed intermediate representation.
2. **System Design Layer** expands intent into architecture: entities, roles, flows, and assumptions.
3. **Schema Generation** emits UI, API, DB, auth, and business-logic configs.
4. **Validation + Repair** checks JSON shape and cross-layer consistency, then repairs specific broken layers.
5. **Runtime Simulation** proves the config can execute by mounting routes, forms, permissions, and seed data in a minimal interpreter.
6. **Evaluation Harness** runs 20 prompts and reports success rate, retries, failures, and latency.

The default path is deterministic and offline, so the same input produces the same normalized config. An LLM can be added behind the stage interfaces without changing validation, repair, or runtime semantics.

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

Open `http://127.0.0.1:8000` and enter a product prompt.

Run tests:

```bash
pytest tests/ -v
```

Run evaluation:

```bash
python -m src.eval.run_eval
```

Latest local evaluation:

- prompts: 20
- real product prompts: 10
- edge cases: 10
- success rate: 100%
- average repairs per request: 0.25
- average deterministic latency: 0.1ms
- failure types after repair: none

## API

`POST /compile`

```json
{
  "prompt": "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics."
}
```

Returns:

- `compiled_config`: strict JSON config
- `validation`: issues before and after repair
- `runtime`: execution simulation results
- `metrics`: latency and repair counts

## Why This Is Reliable

- **Strict contracts:** all public outputs are Pydantic models with required fields.
- **Cross-layer checks:** UI forms must map to APIs, APIs must map to DB tables, auth permissions must map to roles, and business rules must reference real entities.
- **Targeted repair:** validators return typed issue codes. The repair engine patches only the affected layer instead of blindly retrying the whole compilation.
- **Deterministic generation:** canonical ordering, stable IDs, keyword extraction, and zero-temperature-compatible stage boundaries.
- **Execution awareness:** the runtime simulator executes a smoke path for pages, APIs, role permissions, and business gates before returning success.

## Cost vs Quality Tradeoff

The compiler uses a cheap deterministic pass first. In production, the recommended strategy is:

- Run deterministic extraction for common SaaS/product patterns.
- Use a small structured model only for ambiguous intent fields.
- Regenerate individual failed layers, never the full app, when validation reports localized issues.
- Escalate to a stronger model only when repair confidence is low or a prompt contains novel domain terms.

This keeps latency predictable while preserving a path to higher quality when ambiguity is real.
