from app.main import app


def test_api_v1_routers_are_mounted_once():
    paths = {route.path for route in app.routes}

    assert "/api/v1/auth/login" in paths
    assert "/api/v1/users" in paths
    assert "/api/v1/documents/pending" in paths
    assert not any(path.startswith("/api/v1/api/v1") for path in paths)
