# Evaluation Results

Run command:

```bash
python -m src.eval.run_eval
```

Latest run:

```json
{
  "total": 20,
  "success_rate": 1.0,
  "avg_latency_ms": 0.1,
  "avg_repairs": 0.25,
  "failure_types": {}
}
```

Dataset split:

- 10 real product prompts
- 10 edge cases covering vague, conflicting, incomplete, duplicated, and underspecified requirements

Interpretation:

- The deterministic pipeline generated executable configs for all prompts in the dataset.
- Ambiguous prompts triggered targeted repair on specific layers instead of full regeneration.
- Runtime simulation passed after repair for every case.
