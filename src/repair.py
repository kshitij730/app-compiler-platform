from __future__ import annotations

from copy import deepcopy

from .models import ApiEndpoint, CompiledConfig, FieldDef, Permission, Table, ValidationReport


def repair_config(config: CompiledConfig, report: ValidationReport) -> CompiledConfig:
    repaired = deepcopy(config)
    tables = {table.name: table for table in repaired.database.tables}
    endpoints = {f"{ep.method} {ep.path}" for ep in repaired.api.endpoints}
    roles = {role.name for role in repaired.auth.roles} | {"anonymous"}

    for issue in report.issues:
        if issue.code == "TABLE_MISSING_ID":
            table_name = _name_from_message(issue.message, "Table ", " is")
            if table_name in tables:
                tables[table_name].fields.insert(0, FieldDef(name="id", type="uuid"))

        if issue.code in {"UI_FIELD_NOT_IN_DB", "API_REQUEST_FIELD_NOT_IN_DB", "API_RESPONSE_FIELD_NOT_IN_DB"}:
            for table in repaired.database.tables:
                for field in _quoted_list(issue.message):
                    if field not in {f.name for f in table.fields} and table.name in issue.message:
                        table.fields.append(FieldDef(name=field, type=_infer_type(field), required=False))

        if issue.code == "MISSING_ENDPOINT":
            action = issue.message.split(": ", 1)[-1]
            if action not in endpoints:
                method, path = action.split(" ", 1)
                entity = path.split("/")[-1] if path.startswith("/api/") else None
                entity = entity if entity in tables else None
                fields = [f.name for f in tables[entity].fields] if entity else []
                repaired.api.endpoints.append(ApiEndpoint(path=path, method=method, entity=entity, request_fields=[f for f in fields if f != "id"], response_fields=fields, roles=[r for r in roles if r != "anonymous"] or ["user"]))

        if issue.code in {"UNKNOWN_ROLE", "PERMISSION_UNKNOWN_ROLE"}:
            bad_role = issue.message.rsplit(" ", 1)[-1]
            for page in repaired.ui.pages:
                page.roles = ["user" if role == bad_role else role for role in page.roles]
            for endpoint in repaired.api.endpoints:
                endpoint.roles = ["user" if role == bad_role else role for role in endpoint.roles]

        if issue.code == "PERMISSION_UNKNOWN_RESOURCE":
            repaired.auth.permissions = [p for p in repaired.auth.permissions if p.resource in tables]

        if issue.code == "API_ENTITY_NOT_IN_DB":
            entity = issue.message.rsplit(" ", 1)[-1]
            repaired.database.tables.append(Table(name=entity, fields=[FieldDef(name="id", type="uuid"), FieldDef(name="name", type="string")]))

        if issue.code == "RULE_UNKNOWN_ENTITY":
            for rule in repaired.business_logic:
                rule.entities = [entity for entity in rule.entities if entity in tables]

    table_names = {table.name for table in repaired.database.tables}
    existing_permissions = {(p.role, p.resource) for p in repaired.auth.permissions}
    for role in repaired.auth.roles:
        for resource in table_names:
            if (role.name, resource) not in existing_permissions:
                actions = ["create", "read", "update", "delete", "manage"] if role.name == "admin" else ["create", "read", "update"]
                repaired.auth.permissions.append(Permission(role=role.name, resource=resource, actions=actions))

    return repaired


def _infer_type(field: str):
    if "email" in field:
        return "email"
    if "amount" in field or "price" in field or "total" in field:
        return "money"
    if field.endswith("_at"):
        return "datetime"
    if field.endswith("_id") or field == "id":
        return "uuid"
    if field.startswith("is_") or field in {"active", "done"}:
        return "boolean"
    return "string"


def _quoted_list(message: str) -> list[str]:
    if "[" not in message or "]" not in message:
        return []
    raw = message.split("[", 1)[1].split("]", 1)[0]
    return [part.strip().strip("'\"") for part in raw.split(",") if part.strip()]


def _name_from_message(message: str, prefix: str, suffix: str) -> str:
    return message.split(prefix, 1)[1].split(suffix, 1)[0]
