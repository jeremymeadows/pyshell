def command(name):
    def decorator(func):
        global __all__
        __all__ += [name]
        globals()[name] = func
    return decorator


import importlib, pkgutil
__all__ = [module.name for module in pkgutil.iter_modules(__path__)]
for module in __all__:
    vars()[module] = getattr(importlib.import_module(f"{__name__}.{module}"), f"_{module}")