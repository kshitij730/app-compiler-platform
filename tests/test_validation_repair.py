from copy import deepcopy

from src.pipeline import AppCompiler
from src.repair import repair_config
from src.validation import validate_config


def test_repair_adds_missing_endpoint_for_ui_action():
    config = AppCompiler().compile("Build a CRM with contacts and dashboard").compiled_config
    broken = deepcopy(config)
    broken.api.endpoints = [endpoint for endpoint in broken.api.endpoints if endpoint.path != "/api/contacts" or endpoint.method != "POST"]

    before = validate_config(broken)
    repaired = repair_config(broken, before)
    after = validate_config(repaired)

    assert any(issue.code == "MISSING_ENDPOINT" for issue in before.issues)
    assert after.ok


def test_repair_removes_invalid_permission_resource():
    config = AppCompiler().compile("Build a CRM with contacts and dashboard").compiled_config
    broken = deepcopy(config)
    broken.auth.permissions[0].resource = "ghosts"

    before = validate_config(broken)
    repaired = repair_config(broken, before)
    after = validate_config(repaired)

    assert any(issue.code == "PERMISSION_UNKNOWN_RESOURCE" for issue in before.issues)
    assert after.ok
