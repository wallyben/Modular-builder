"""Adapter system for the Modular AI Execution Engine.

Public surface
--------------
Adapter
    Callable protocol that every adapter must satisfy.
AdapterRegistry
    Registry that maps string names to adapter callables.
default_registry
    Pre-populated registry with all built-in adapters.

Built-in adapters (registered on import)
-----------------------------------------
``echo``   — returns step params unchanged; useful for no-ops / tests.
``http``   — executes an HTTP request via httpx.
``fail``   — always raises; useful for testing failure paths.
"""

from core.adapters.base import Adapter
from core.adapters.builtin import echo_adapter, fail_adapter, http_adapter
from core.adapters.builtin.llm import llm_anthropic_adapter, llm_openai_adapter
from core.adapters.registry import AdapterRegistry, default_registry

# -----------------------------------------------------------------------
# Register built-ins into the shared default registry
# -----------------------------------------------------------------------
default_registry.register("echo", echo_adapter)
default_registry.register("http", http_adapter)
default_registry.register("fail", fail_adapter)
default_registry.register("llm.openai", llm_openai_adapter)
default_registry.register("llm.anthropic", llm_anthropic_adapter)

__all__ = [
    "Adapter",
    "AdapterRegistry",
    "default_registry",
]
