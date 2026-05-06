from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class FieldDef(BaseModel):
    name: str
    type: Literal["string", "text", "integer", "number", "boolean", "datetime", "uuid", "email", "money"]
    required: bool = True
    unique: bool = False
    references: str | None = None


class Entity(BaseModel):
    name: str
    fields: list[FieldDef]
    owner_role: str | None = None


class Role(BaseModel):
    name: str
    description: str


class Feature(BaseModel):
    name: str
    enabled: bool = True
    details: dict[str, Any] = Field(default_factory=dict)


class IntentIR(BaseModel):
    app_name: str
    domain: str
    features: list[Feature]
    entities: list[Entity]
    roles: list[Role]
    assumptions: list[str] = Field(default_factory=list)
    clarifying_questions: list[str] = Field(default_factory=list)


class Flow(BaseModel):
    name: str
    actor: str
    steps: list[str]


class SystemDesign(BaseModel):
    app_name: str
    entities: list[Entity]
    roles: list[Role]
    flows: list[Flow]
    assumptions: list[str]


class UIComponent(BaseModel):
    id: str
    type: Literal["table", "form", "chart", "metric", "nav", "button", "text"]
    entity: str | None = None
    fields: list[str] = Field(default_factory=list)
    action: str | None = None


class UIPage(BaseModel):
    path: str
    title: str
    roles: list[str]
    components: list[UIComponent]


class UIConfig(BaseModel):
    pages: list[UIPage]


class ApiEndpoint(BaseModel):
    path: str
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    entity: str | None = None
    request_fields: list[str] = Field(default_factory=list)
    response_fields: list[str] = Field(default_factory=list)
    roles: list[str]


class APIConfig(BaseModel):
    endpoints: list[ApiEndpoint]


class Table(BaseModel):
    name: str
    fields: list[FieldDef]


class DBConfig(BaseModel):
    tables: list[Table]


class Permission(BaseModel):
    role: str
    resource: str
    actions: list[Literal["create", "read", "update", "delete", "manage"]]


class AuthConfig(BaseModel):
    login_required: bool
    roles: list[Role]
    permissions: list[Permission]


class BusinessRule(BaseModel):
    id: str
    description: str
    condition: str
    effect: str
    entities: list[str] = Field(default_factory=list)


class CompiledConfig(BaseModel):
    app_name: str
    version: str = "1.0"
    ui: UIConfig
    api: APIConfig
    database: DBConfig
    auth: AuthConfig
    business_logic: list[BusinessRule]
    assumptions: list[str]


class ValidationIssue(BaseModel):
    code: str
    severity: Severity
    layer: Literal["json", "ui", "api", "database", "auth", "business_logic", "runtime"]
    message: str
    path: str


class ValidationReport(BaseModel):
    ok: bool
    issues: list[ValidationIssue] = Field(default_factory=list)


class RuntimeReport(BaseModel):
    executable: bool
    mounted_pages: list[str]
    mounted_endpoints: list[str]
    smoke_tests: list[str]
    issues: list[ValidationIssue] = Field(default_factory=list)


class CompileMetrics(BaseModel):
    latency_ms: int
    repair_iterations: int
    issue_count_before_repair: int
    issue_count_after_repair: int


class CompileRequest(BaseModel):
    prompt: str = Field(min_length=3)


class CompileResponse(BaseModel):
    compiled_config: CompiledConfig
    validation_before_repair: ValidationReport
    validation_after_repair: ValidationReport
    runtime: RuntimeReport
    metrics: CompileMetrics
