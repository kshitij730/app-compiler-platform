from __future__ import annotations

from .models import CompiledConfig, RuntimeReport, Severity, ValidationIssue


def simulate_runtime(config: CompiledConfig) -> RuntimeReport:
    issues: list[ValidationIssue] = []
    endpoints = {f"{ep.method} {ep.path}": ep for ep in config.api.endpoints}
    tables = {table.name: table for table in config.database.tables}
    mounted_pages = []
    smoke_tests = []

    for page in config.ui.pages:
        mounted_pages.append(page.path)
        for component in page.components:
            if component.action and component.action not in endpoints:
                issues.append(_runtime_issue(f"Unroutable component action {component.action}", page.path))
            if component.entity and component.entity not in tables:
                issues.append(_runtime_issue(f"Missing data source {component.entity}", page.path))
        smoke_tests.append(f"render:{page.path}")

    for key, endpoint in endpoints.items():
        if endpoint.entity and endpoint.entity not in tables:
            issues.append(_runtime_issue(f"Endpoint {key} cannot bind table {endpoint.entity}", endpoint.path))
        smoke_tests.append(f"route:{key}")

    for rule in config.business_logic:
        if "premium" in rule.id:
            has_billing = any(ep.path == "/api/billing/checkout" for ep in endpoints.values())
            if not has_billing:
                issues.append(_runtime_issue("Premium rule exists without billing checkout endpoint", "business_logic"))
            smoke_tests.append("business:premium_gate")

    return RuntimeReport(
        executable=not issues,
        mounted_pages=mounted_pages,
        mounted_endpoints=list(endpoints.keys()),
        smoke_tests=smoke_tests,
        issues=issues,
    )


def _runtime_issue(message: str, path: str) -> ValidationIssue:
    return ValidationIssue(code="RUNTIME_BINDING_FAILED", severity=Severity.ERROR, layer="runtime", message=message, path=path)
