from __future__ import annotations

import json
import statistics
from collections import Counter

from src.eval.prompts import ALL_PROMPTS
from src.pipeline import AppCompiler


def main() -> None:
    compiler = AppCompiler()
    rows = []
    failures = Counter()

    for prompt in ALL_PROMPTS:
        result = compiler.compile(prompt)
        success = result.validation_after_repair.ok and result.runtime.executable
        for issue in result.validation_after_repair.issues:
            failures[issue.code] += 1
        rows.append(
            {
                "prompt": prompt,
                "success": success,
                "latency_ms": result.metrics.latency_ms,
                "repairs": result.metrics.repair_iterations,
                "issues_before": result.metrics.issue_count_before_repair,
                "issues_after": result.metrics.issue_count_after_repair,
            }
        )

    success_rate = sum(1 for row in rows if row["success"]) / len(rows)
    summary = {
        "total": len(rows),
        "success_rate": round(success_rate, 3),
        "avg_latency_ms": round(statistics.mean(row["latency_ms"] for row in rows), 2),
        "avg_repairs": round(statistics.mean(row["repairs"] for row in rows), 2),
        "failure_types": dict(failures),
        "results": rows,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
