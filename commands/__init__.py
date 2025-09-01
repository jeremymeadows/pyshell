import importlib
import pkgutil

__all__ = [module.name for module in pkgutil.iter_modules(__path__)]
for module in __all__:
    vars()[module] = getattr(importlib.import_module(f"{__name__}.{module}"), module)