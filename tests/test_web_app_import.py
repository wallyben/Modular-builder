"""Smoke test: ensure the FastAPI app can be imported without errors."""


def test_app_imports() -> None:
    from web.app import app  # noqa: F401
    from fastapi import FastAPI

    assert isinstance(app, FastAPI), "web.app.app must be a FastAPI instance"


def test_routes_registered() -> None:
    from web.app import app

    paths = {route.path for route in app.routes}
    assert "/" in paths
    assert "/tender" in paths
    assert "/prospect" in paths
    assert "/download-docx" in paths
