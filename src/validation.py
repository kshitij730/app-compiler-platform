from __future__ import annotations

from .models import CompiledConfig, Severity, ValidationIssue, ValidationReport


def validate_config(config: CompiledConfig) -> ValidationReport:
    issues: list[ValidationIssue] = []
    table_names = {table.name for table in config.database.tables}
    role_names = {role.name for role in config.auth.roles} | {"anonymous"}
    endpoint_keys = {f"{ep.method} {ep.path}" for ep in config.api.endpoints}
    table_fields = {table.name: {field.name for field in table.fields} for table in config.database.tables}

    for page_index, page in enumerate(config.ui.pages):
        for role in page.roles:
            if role not in role_names:
                issues.append(_issue("UNKNOWN_ROLE", "ui", f"UI page references unknown role {role}", f"ui.pages[{page_index}].roles"))
        for comp_index, component in enumerate(page.components):
            if component.entity and component.entity not in table_names:
                issues.append(_issue("UNKNOWN_ENTITY", "ui", f"Component references missing table {component.entity}", f"ui.pages[{page_index}].components[{comp_index}].entity"))
            if component.action and component.action not in endpoint_keys:
                issues.append(_issue("MISSING_ENDPOINT", "ui", f"Component action has no API endpoint: {component.action}", f"ui.pages[{page_index}].components[{comp_index}].action"))
            if component.entity in table_fields:
                missing = set(component.fields) - table_fields[component.entity]
                if missing:
                    issues.append(_issue("UI_FIELD_NOT_IN_DB", "ui", f"UI fields not in DB table {component.entity}: {sorted(missing)}", f"ui.pages[{page_index}].components[{comp_index}].fields"))

    for ep_index, endpoint in enumerate(config.api.endpoints):
        for role in endpoint.roles:
            if role not in role_names:
                issues.append(_issue("UNKNOWN_ROLE", "api", f"API endpoint references unknown role {role}", f"api.endpoints[{ep_index}].roles"))
        if endpoint.entity:
            if endpoint.entity not in table_names:
                issues.append(_issue("API_ENTITY_NOT_IN_DB", "api", f"Endpoint references missing table {endpoint.entity}", f"api.endpoints[{ep_index}].entity"))
                continue
            allowed = table_fields[endpoint.entity]
            bad_request = set(endpoint.request_fields) - allowed
            bad_response = set(endpoint.response_fields) - allowed
            if bad_request:
                issues.append(_issue("API_REQUEST_FIELD_NOT_IN_DB", "api", f"Request fields not in DB table {endpoint.entity}: {sorted(bad_request)}", f"api.endpoints[{ep_index}].request_fields"))
            if bad_response:
                issues.append(_issue("API_RESPONSE_FIELD_NOT_IN_DB", "api", f"Response fields not in DB table {endpoint.entity}: {sorted(bad_response)}", f"api.endpoints[{ep_index}].response_fields"))

    for table_index, table in enumerate(config.database.tables):
        names = [field.name for field in table.fields]
        if "id" not in names:
            issues.append(_issue("TABLE_MISSING_ID", "database", f"Table {table.name} is missing id field", f"database.tables[{table_index}].fields"))
        if len(names) != len(set(names)):
            issues.append(_issue("DUPLICATE_DB_FIELD", "database", f"Table {table.name} has duplicate fields", f"database.tables[{table_index}].fields"))
        for field_index, field in enumerate(table.fields):
            if field.references and field.references not in table_names:
                issues.append(_issue("BROKEN_REFERENCE", "database", f"{table.name}.{field.name} references missing table {field.references}", f"database.tables[{table_index}].fields[{field_index}]"))

    for perm_index, permission in enumerate(config.auth.permissions):
        if permission.role not in role_names:
            issues.append(_issue("PERMISSION_UNKNOWN_ROLE", "auth", f"Permission references unknown role {permission.role}", f"auth.permissions[{perm_index}].role"))
        if permission.resource not in table_names:
            issues.append(_issue("PERMISSION_UNKNOWN_RESOURCE", "auth", f"Permission references missing resource {permission.resource}", f"auth.permissions[{perm_index}].resource"))

    for rule_index, rule in enumerate(config.business_logic):
        for entity in rule.entities:
            if entity not in table_names:
                issues.append(_issue("RULE_UNKNOWN_ENTITY", "business_logic", f"Rule {rule.id} references missing entity {entity}", f"business_logic[{rule_index}].entities"))

    return ValidationReport(ok=not any(issue.severity == Severity.ERROR for issue in issues), issues=issues)


def _issue(code: str, layer: str, message: str, path: str) -> ValidationIssue:
    return ValidationIssue(code=code, severity=Severity.ERROR, layer=layer, message=message, path=path)
