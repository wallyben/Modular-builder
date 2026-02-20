from __future__ import annotations

from typing import Dict

from core.adapters.base import Adapter
from core.schemas import Step


class AdapterRegistry:
    """Central registry that maps adapter names to callables.

    Usage
    -----
    >>> registry = AdapterRegistry()
    >>> registry.register("echo", echo_adapter)
    >>> adapter = registry.get("echo")
    >>> result = adapter(step)

    The registry is intentionally not a singleton so that tests can build
    isolated instances without touching global state.  A pre-populated global
    ``default_registry`` is provided for production use.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Adapter] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, name: str, adapter: Adapter) -> None:
        """Register *adapter* under *name*.

        Overwrites any previously registered adapter with the same name,
        which allows tests and plugins to replace built-ins cleanly.
        """
        if not callable(adapter):
            raise TypeError(f"adapter must be callable, got {type(adapter)!r}")
        self._registry[name] = adapter

    def unregister(self, name: str) -> None:
        """Remove *name* from the registry (no-op if not present)."""
        self._registry.pop(name, None)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, name: str) -> Adapter:
        """Return the adapter registered under *name*.

        Raises
        ------
        KeyError
            If no adapter with that name has been registered.
        """
        try:
            return self._registry[name]
        except KeyError:
            available = ", ".join(sorted(self._registry)) or "<none>"
            raise KeyError(
                f"No adapter registered for {name!r}. "
                f"Available: {available}"
            ) from None

    def __contains__(self, name: str) -> bool:
        return name in self._registry

    def registered_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._registry))


# ---------------------------------------------------------------------------
# Module-level default registry — populated by core/adapters/__init__.py
# ---------------------------------------------------------------------------

default_registry: AdapterRegistry = AdapterRegistry()
