import os, socket, sys

from pyshell.utils.termcolors import fg as color


def prompt():
    return f"{color.green}{{cwd}}{color.white}\n> "

class PyShellEnv:
    def __init__(self):
        self.namespace = { "prompt": prompt }
        self.interactive = sys.stdin.isatty()
        self.repl = True
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