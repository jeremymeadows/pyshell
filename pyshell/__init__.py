import os, socket, sys

__version__ = "0.1.0"


def prompt():
    return f"{{user}} {{cwd}} > "

class PyShellEnv:
    def __init__(self):
        self.namespace = { "prompt": prompt }
        self.interactive = sys.stdin.isatty()
        self.repl = True
        self.help = ""
        self.aliases = dict()
        self.prompt_subs = {
            "user": os.getlogin(),
            "host": socket.gethostname(),
            "cwd": lambda: os.path.join(os.getcwd().replace(os.getenv("HOME", "~"), "~"), ""),
        }

pyshenv = PyShellEnv()


import importlib, pkgutil
__all__ = [module.name for module in pkgutil.iter_modules(__path__) if module.name != '__main__']
for module in __all__:
    importlib.import_module(f"{__name__}.{module}")
__all__ += ["pyshenv"]