# Auto-discover and register all service modules in this package
from importlib import import_module
from pathlib import Path

_registry: dict[int, "BaseService"] = {}


def register(service_id: int):
    """Decorator — registers a service class by its sickw service ID."""
    def decorator(cls):
        _registry[service_id] = cls()
        return cls
    return decorator


def get(service_id: int):
    """Return the service handler for the given ID, or None."""
    return _registry.get(service_id)


def _autodiscover():
    pkg_dir = Path(__file__).parent
    for path in sorted(pkg_dir.glob("svc_*.py")):
        import_module(f"services.{path.stem}")


_autodiscover()
