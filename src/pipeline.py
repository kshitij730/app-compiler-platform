from __future__ import annotations

import re
import time
from copy import deepcopy

from .models import (
    APIConfig,
    ApiEndpoint,
    AuthConfig,
    BusinessRule,
    CompileMetrics,
    CompileResponse,
    CompiledConfig,
    DBConfig,
    Entity,
    Feature,
    FieldDef,
    Flow,
    IntentIR,
    Permission,
    Role,
    RuntimeReport,
    SystemDesign,
    Table,
    UIComponent,
    UIConfig,
    UIPage,
)
from .repair import repair_config
from .runtime import simulate_runtime
from .validation import validate_config


STOPWORDS = {"a", "an", "the", "with", "for", "and", "to", "of", "app", "application", "build", "create", "make"}

ENTITY_CATALOG: dict[str, list[FieldDef]] = {
    "contacts": [
        FieldDef(name="id", type="uuid"),
        FieldDef(name="name", type="string"),
        FieldDef(name="email", type="email", unique=True),
        FieldDef(name="company", type="string", required=False),
        FieldDef(name="status", type="string", required=False),
    ],
    "companies": [
        FieldDef(name="id", type="uuid"),
        FieldDef(name="name", type="string", unique=True),
        FieldDef(name="industry", type="string", required=False),
        FieldDef(name="website", type="string", required=False),
    ],
    "deals": [
        FieldDef(name="id", type="uuid"),
        FieldDef(name="title", type="string"),
        FieldDef(name="amount", type="money"),
        FieldDef(name="stage", type="string"),
        FieldDef(name="contact_id", type="uuid", references="contacts", required=False),
    ],
    "tasks": [
        FieldDef(name="id", type="uuid"),
        FieldDef(name="title", type="string"),
        FieldDef(name="done", type="boolean", required=False),
        FieldDef(name="due_at", type="datetime", required=False),
    ],
    "invoices": [
        FieldDef(name="id", type="uuid"),
        FieldDef(name="customer_email", type="email"),
        FieldDef(name="amount", type="money"),
        FieldDef(name="status", type="string"),
    ],
    "products": [
        FieldDef(name="id", type="uuid"),
        FieldDef(name="name", type="string"),
        FieldDef(name="price", type="money"),
        FieldDef(name="active", type="boolean", required=False),
    ],
    "orders": [
        FieldDef(name="id", type="uuid"),
        FieldDef(name="customer_email", type="email"),
        FieldDef(name="total", type="money"),
        FieldDef(name="status", type="string"),
    ],
    "tickets": [
        FieldDef(name="id", type="uuid"),
        FieldDef(name="subject", type="string"),
        FieldDef(name="priority", type="string"),
        FieldDef(name="status", type="string"),
    ],
    "projects": [
        FieldDef(name="id", type="uuid"),
        FieldDef(name="name", type="string"),
        FieldDef(name="status", type="string"),
        FieldDef(name="owner_email", type="email", required=False),
    ],
    "users": [
        FieldDef(name="id", type="uuid"),
        FieldDef(name="email", type="email", unique=True),
        FieldDef(name="role", type="string"),
        FieldDef(name="created_at", type="datetime"),
    ],
}

FEATURE_KEYWORDS = {
    "auth": ["login", "auth", "signup", "password"],
    "dashboard": ["dashboard", "metrics", "overview"],
    "analytics": ["analytics", "reports", "chart", "insights"],
    "payments": ["payment", "payments", "billing", "premium", "subscription", "stripe"],
    "rbac": ["role", "roles", "admin", "permission", "access"],
    "notifications": ["email", "notification", "notify"],
    "search": ["search", "filter"],
}


class AppCompiler:
    def compile(self, prompt: str) -> CompileResponse:
        started = time.perf_counter()
        intent = self.extract_intent(prompt)
        design = self.design_system(intent)
        config = self.generate_schema(design, intent)
        before = validate_config(config)

        repaired = deepcopy(config)
        iterations = 0
        while iterations < 3:
            report = validate_config(repaired)
            if report.ok:
                break
            repaired = repair_config(repaired, report)
            iterations += 1

        after = validate_config(repaired)
        runtime = simulate_runtime(repaired)
        if runtime.issues:
            after.issues.extend(runtime.issues)
            after.ok = False

        latency_ms = int((time.perf_counter() - started) * 1000)
        return CompileResponse(
            compiled_config=repaired,
            validation_before_repair=before,
            validation_after_repair=after,
            runtime=runtime,
            metrics=CompileMetrics(
                latency_ms=latency_ms,
                repair_iterations=iterations,
                issue_count_before_repair=len(before.issues),
                issue_count_after_repair=len(after.issues),
            ),
        )

    def extract_intent(self, prompt: str) -> IntentIR:
        text = prompt.lower()
        app_name = self._app_name(text)
        domain = self._domain(text)
        features = [Feature(name=name) for name, words in FEATURE_KEYWORDS.items() if any(w in text for w in words)]
        if not features:
            features = [Feature(name="crud"), Feature(name="dashboard")]

        entities = [Entity(name=name, fields=fields) for name, fields in ENTITY_CATALOG.items() if self._mentions_entity(text, name)]
        if not entities:
            entities = [Entity(name="users", fields=ENTITY_CATALOG["users"]), Entity(name="projects", fields=ENTITY_CATALOG["projects"])]

        roles = [Role(name="user", description="Default authenticated user")]
        if any(word in text for word in ["admin", "analytics", "manage", "role"]):
            roles.append(Role(name="admin", description="Can manage system settings and analytics"))
        if any(word in text for word in ["client", "customer", "buyer"]):
            roles.append(Role(name="customer", description="External customer account"))

        assumptions = []
        questions = []
        if len(prompt.split()) < 8:
            assumptions.append("Prompt is underspecified, so a standard CRUD dashboard app is generated.")
            questions.append("Which primary workflow should be optimized first?")
        if "premium" in text or "payments" in text:
            assumptions.append("Payments are represented as a Stripe-compatible subscription gate.")
        if "login" in text and "auth" not in [f.name for f in features]:
            features.append(Feature(name="auth"))
        if not any(e.name == "users" for e in entities):
            entities.append(Entity(name="users", fields=ENTITY_CATALOG["users"]))

        return IntentIR(app_name=app_name, domain=domain, features=features, entities=entities, roles=roles, assumptions=assumptions, clarifying_questions=questions)

    def design_system(self, intent: IntentIR) -> SystemDesign:
        flows = [
            Flow(name="authenticate", actor="user", steps=["open login", "submit credentials", "receive session"]),
            Flow(name="manage_records", actor="user", steps=["open dashboard", "view records", "create or update entity"]),
        ]
        if any(f.name == "payments" for f in intent.features):
            flows.append(Flow(name="upgrade_plan", actor="user", steps=["open billing", "start checkout", "activate premium"]))
        if any(role.name == "admin" for role in intent.roles):
            flows.append(Flow(name="admin_analytics", actor="admin", steps=["open analytics", "review metrics", "export report"]))
        return SystemDesign(app_name=intent.app_name, entities=intent.entities, roles=intent.roles, flows=flows, assumptions=intent.assumptions)

    def generate_schema(self, design: SystemDesign, intent: IntentIR) -> CompiledConfig:
        pages = [
            UIPage(path="/login", title="Login", roles=["anonymous"], components=[UIComponent(id="login-form", type="form", entity="users", fields=["email"], action="POST /api/auth/login")]),
            UIPage(path="/dashboard", title="Dashboard", roles=[r.name for r in design.roles], components=[UIComponent(id="main-nav", type="nav"), UIComponent(id="summary", type="metric")]),
        ]
        endpoints = [ApiEndpoint(path="/api/auth/login", method="POST", entity="users", request_fields=["email"], response_fields=["id", "email", "role"], roles=["anonymous"])]
        tables = [Table(name=e.name, fields=e.fields) for e in design.entities]

        for entity in design.entities:
            if entity.name == "users":
                continue
            field_names = [f.name for f in entity.fields]
            pages.append(
                UIPage(
                    path=f"/{entity.name}",
                    title=entity.name.title(),
                    roles=[r.name for r in design.roles],
                    components=[
                        UIComponent(id=f"{entity.name}-table", type="table", entity=entity.name, fields=field_names, action=f"GET /api/{entity.name}"),
                        UIComponent(id=f"{entity.name}-form", type="form", entity=entity.name, fields=[f.name for f in entity.fields if f.name != "id"], action=f"POST /api/{entity.name}"),
                    ],
                )
            )
            endpoints.extend(
                [
                    ApiEndpoint(path=f"/api/{entity.name}", method="GET", entity=entity.name, response_fields=field_names, roles=[r.name for r in design.roles]),
                    ApiEndpoint(path=f"/api/{entity.name}", method="POST", entity=entity.name, request_fields=[f for f in field_names if f != "id"], response_fields=field_names, roles=[r.name for r in design.roles]),
                ]
            )

        permissions = []
        for role in design.roles:
            actions = ["create", "read", "update", "delete", "manage"] if role.name == "admin" else ["create", "read", "update"]
            for entity in design.entities:
                permissions.append(Permission(role=role.name, resource=entity.name, actions=actions))

        rules = []
        if any(f.name == "payments" for f in intent.features):
            rules.append(BusinessRule(id="premium_gate", description="Premium-only features require an active subscription.", condition="user.subscription_status == 'active'", effect="allow premium routes", entities=["users"]))
            tables.append(Table(name="subscriptions", fields=[FieldDef(name="id", type="uuid"), FieldDef(name="user_id", type="uuid", references="users"), FieldDef(name="status", type="string"), FieldDef(name="provider_customer_id", type="string")]))
            endpoints.append(ApiEndpoint(path="/api/billing/checkout", method="POST", entity="subscriptions", request_fields=["user_id"], response_fields=["id", "status"], roles=["user", "admin"]))
            pages.append(UIPage(path="/billing", title="Billing", roles=["user", "admin"], components=[UIComponent(id="plan-status", type="metric", entity="subscriptions", fields=["status"]), UIComponent(id="checkout", type="button", action="POST /api/billing/checkout")]))
        if any(f.name == "analytics" for f in intent.features):
            pages.append(UIPage(path="/analytics", title="Analytics", roles=["admin"], components=[UIComponent(id="analytics-chart", type="chart", fields=["count", "trend"], action="GET /api/analytics")]))
            endpoints.append(ApiEndpoint(path="/api/analytics", method="GET", response_fields=["count", "trend"], roles=["admin"]))

        return CompiledConfig(
            app_name=design.app_name,
            ui=UIConfig(pages=pages),
            api=APIConfig(endpoints=endpoints),
            database=DBConfig(tables=tables),
            auth=AuthConfig(login_required=True, roles=design.roles, permissions=permissions),
            business_logic=rules,
            assumptions=design.assumptions,
        )

    def _mentions_entity(self, text: str, entity: str) -> bool:
        singular = entity[:-1] if entity.endswith("s") else entity
        aliases = {"contacts": ["crm", "lead", "leads"], "deals": ["crm", "pipeline"], "companies": ["crm", "accounts"], "tickets": ["support", "helpdesk"], "orders": ["ecommerce", "shop"], "products": ["ecommerce", "shop"]}
        return entity in text or singular in text or any(alias in text for alias in aliases.get(entity, []))

    def _domain(self, text: str) -> str:
        if "crm" in text or "lead" in text:
            return "crm"
        if "ecommerce" in text or "shop" in text:
            return "commerce"
        if "support" in text or "ticket" in text:
            return "support"
        if "invoice" in text or "billing" in text:
            return "finance"
        return "productivity"

    def _app_name(self, text: str) -> str:
        words = [re.sub(r"[^a-z0-9]", "", w) for w in text.split()]
        meaningful = [w for w in words if w and w not in STOPWORDS]
        if not meaningful:
            return "Generated App"
        return " ".join(meaningful[:3]).title()
