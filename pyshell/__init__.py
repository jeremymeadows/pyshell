import importlib
import pkgutil

__all__ = [module.name for module in pkgutil.iter_modules(__path__) if module.name != '__main__']
for module in __all__:
    importlib.import_module(f"{__name__}.{module}")


import os, socket, sys

pyshenv = type("PyShellEnv", (object,), {
    "namespace": dict(),
    "run": lambda: None,
    "interactive": sys.stdin.isatty(),
    "noexit": False,
    "aliases": dict(),
    "prompt_subs": {
        "user": os.getlogin(),
        "host": socket.gethostname(),
        "cwd": lambda: os.path.join(os.getcwd().replace(os.getenv("HOME", "~"), "~"), ""),
    },
})()


def prompt():
    from pyshell.utils.termcolors import fg as color
    return f"{color.green}{{cwd}}{color.white}\n> "


__all__ += [pyshenv, prompt]