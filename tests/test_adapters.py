"""Tests for the adapter system (registry + built-ins)."""
from __future__ import annotations

import pytest

from core.adapters import AdapterRegistry, default_registry
from core.adapters.builtin.echo import echo_adapter
from core.adapters.builtin.fail import fail_adapter
from core.schemas import Step


def _step(adapter: str = "echo", params: dict | None = None) -> Step:
    return Step(id="s1", name="s1", adapter=adapter, params=params or {})


# ---------------------------------------------------------------------------
# AdapterRegistry
# ---------------------------------------------------------------------------

class TestAdapterRegistry:
    def test_register_and_get(self):
        reg = AdapterRegistry()
        reg.register("echo", echo_adapter)
        assert reg.get("echo") is echo_adapter

    def test_get_unknown_raises_keyerror(self):
        reg = AdapterRegistry()
        with pytest.raises(KeyError, match="No adapter registered"):
            reg.get("nonexistent")

    def test_contains(self):
        reg = AdapterRegistry()
        reg.register("echo", echo_adapter)
        assert "echo" in reg
        assert "nope" not in reg

    def test_unregister(self):
        reg = AdapterRegistry()
        reg.register("echo", echo_adapter)
        reg.unregister("echo")
        assert "echo" not in reg

    def test_unregister_unknown_is_noop(self):
        reg = AdapterRegistry()
        reg.unregister("ghost")  # should not raise

    def test_register_non_callable_raises(self):
        reg = AdapterRegistry()
        with pytest.raises(TypeError):
            reg.register("bad", "not_a_callable")  # type: ignore[arg-type]

    def test_overwrite_registration(self):
        reg = AdapterRegistry()
        reg.register("x", echo_adapter)
        reg.register("x", fail_adapter)
        assert reg.get("x") is fail_adapter

    def test_registered_names_sorted(self):
        reg = AdapterRegistry()
        reg.register("c", echo_adapter)
        reg.register("a", echo_adapter)
        reg.register("b", echo_adapter)
        assert reg.registered_names() == ("a", "b", "c")


# ---------------------------------------------------------------------------
# default_registry built-ins
# ---------------------------------------------------------------------------

class TestDefaultRegistry:
    def test_echo_registered(self):
        assert "echo" in default_registry

    def test_http_registered(self):
        assert "http" in default_registry

    def test_fail_registered(self):
        assert "fail" in default_registry


# ---------------------------------------------------------------------------
# echo adapter
# ---------------------------------------------------------------------------

class TestEchoAdapter:
    def test_returns_params(self):
        s = _step(adapter="echo", params={"key": "value", "num": 42})
        result = echo_adapter(s)
        assert result["params"] == {"key": "value", "num": 42}
        assert result["adapter"] == "echo"
        assert result["step_id"] == "s1"

    def test_empty_params(self):
        result = echo_adapter(_step())
        assert result["params"] == {}


# ---------------------------------------------------------------------------
# fail adapter
# ---------------------------------------------------------------------------

class TestFailAdapter:
    def test_always_raises(self):
        with pytest.raises(RuntimeError, match="deliberate failure"):
            fail_adapter(_step(adapter="fail"))

    def test_custom_message(self):
        s = _step(adapter="fail", params={"message": "boom"})
        with pytest.raises(RuntimeError, match="boom"):
            fail_adapter(s)
