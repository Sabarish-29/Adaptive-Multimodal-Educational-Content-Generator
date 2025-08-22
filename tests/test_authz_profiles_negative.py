import importlib
from fastapi.testclient import TestClient


def reload_profiles(test_mode: bool):
    import os

    os.environ["TEST_MODE"] = "true" if test_mode else "false"
    if "services.profiles.profiles.main" in importlib.sys.modules:
        del importlib.sys.modules["services.profiles.profiles.main"]
    mod = importlib.import_module("services.profiles.profiles.main")
    return mod.app, mod


def test_profiles_learner_forbidden_other_profile():
    app, _ = reload_profiles(test_mode=False)
    client = TestClient(app)
    resp = client.get("/v1/learners/other_user/profile")
    assert resp.status_code == 403


def test_profiles_educator_can_probe_not_found():
    import os

    os.environ["TEST_FORCE_SUB"] = "edu_1"
    os.environ["TEST_FORCE_ROLES"] = "educator"
    app, mod = reload_profiles(test_mode=False)
    client = TestClient(app)
    resp = client.get("/v1/learners/missing_learner/profile")
    assert resp.status_code == 404
