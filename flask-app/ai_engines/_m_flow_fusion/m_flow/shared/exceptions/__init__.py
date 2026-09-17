# m_flow.shared.exceptions
#
# Lazy-loaded public symbols for this sub-package.  The mapping below
# drives ``__getattr__`` so that heavy transitive deps are only pulled
# in when the name is actually accessed.

_EXPORTS = {
    "IngestionError": ("m_flow.shared.exceptions.exceptions", "IngestionError"),
}


def __getattr__(name: str):
    if name in _EXPORTS:
        mod_path, attr = _EXPORTS[name]
        import importlib

        return getattr(importlib.import_module(mod_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_EXPORTS)
