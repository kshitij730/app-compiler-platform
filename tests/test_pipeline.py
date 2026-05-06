from src.pipeline import AppCompiler


def test_crm_prompt_compiles_to_executable_config():
    result = AppCompiler().compile("Build a CRM with login, contacts, dashboard, role-based access, premium plan with payments. Admins can see analytics.")

    assert result.validation_after_repair.ok
    assert result.runtime.executable
    assert any(page.path == "/contacts" for page in result.compiled_config.ui.pages)
    assert any(endpoint.path == "/api/billing/checkout" for endpoint in result.compiled_config.api.endpoints)
    assert any(rule.id == "premium_gate" for rule in result.compiled_config.business_logic)


def test_vague_prompt_documents_assumptions():
    result = AppCompiler().compile("Build an app.")

    assert result.validation_after_repair.ok
    assert result.compiled_config.assumptions
    assert result.runtime.executable


def test_same_input_is_deterministic():
    compiler = AppCompiler()
    left = compiler.compile("Build a support app with tickets, dashboard, login and admin analytics.").compiled_config.model_dump()
    right = compiler.compile("Build a support app with tickets, dashboard, login and admin analytics.").compiled_config.model_dump()

    assert left == right
