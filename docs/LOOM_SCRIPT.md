# Loom Walkthrough Script

Target length: 5-10 minutes.

## 1. Problem Framing

This project behaves like a compiler for app generation. A user prompt is not sent to one giant prompt. It moves through typed stages: intent extraction, system design, schema generation, validation, repair, and runtime simulation.

## 2. Pipeline

Show `src/pipeline.py`.

- `extract_intent` creates the intermediate representation: domain, features, entities, roles, assumptions, and clarifying questions.
- `design_system` turns intent into architecture: entities, flows, roles, and ownership assumptions.
- `generate_schema` emits UI, API, database, auth, and business logic configs.

Explain that the stage boundaries are intentional. In production, an LLM can power a stage, but each stage must still return a typed object.

## 3. Strict Contract

Show `src/models.py`.

Every public output is a Pydantic model. This guarantees required fields, type safety, stable JSON serialization, and a clear contract for a runtime.

## 4. Validation + Repair

Show `src/validation.py` and `src/repair.py`.

Validation checks cross-layer consistency:

- UI actions must map to API endpoints.
- UI/API fields must exist in DB tables.
- permissions must reference real roles and resources.
- business rules must reference real entities.

Repair is targeted. If a UI action is missing an endpoint, only that endpoint is created. If a field is missing from a table, only that field is added. The system does not blindly rerun the entire generation.

## 5. Execution Awareness

Show `src/runtime.py`.

The runtime simulator mounts pages and endpoints, binds UI components to data sources, checks business gates, and returns an executable flag. The API only reports success when validation and runtime simulation both pass.

## 6. Evaluation

Show `src/eval/prompts.py` and run:

```bash
python -m src.eval.run_eval
```

Current metrics:

- 20 prompts total
- 10 real product prompts
- 10 edge cases
- success rate: 100%
- average repairs per request: 0.25
- average latency: about 0.1ms in deterministic local mode
- failure types after repair: none

## 7. Cost vs Quality

The system uses deterministic generation first because it is cheap, fast, and stable. A production version would call a small structured model only for ambiguous extraction, then use a stronger model only for failed or novel stages. Validation and repair stay model-independent.

## 8. Demo

Open the web UI, paste:

```text
Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics.
```

Show the generated config tab, validation tab, and runtime tab.
