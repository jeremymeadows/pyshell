import os
import glob
import readline


class PyShellCompleter():
    def __init__(self):
        self.buf = ""
        self.prefixes = dict()
        self.bins = []
        for path in os.getenv("PATH", "").split(os.pathsep):
            try:
                for file in os.listdir(path):
                    if os.access(os.path.join(path, file), os.X_OK):
                        self.bins += [file]
            except FileNotFoundError:
                pass
        self.bins = sorted(set(self.bins))
    
    def register(self, entries):
        for prefix, options in entries.items():
            self.prefixes[prefix] = options

    def complete(self, text, state):
        if state == 0:
            self.buf = readline.get_line_buffer()
            if self.buf != self.buf.rstrip():
                self.buf += "\x00"
 
        if " " not in self.buf:
            options = self.bins
        else:
            options = self.prefixes.get(self.buf.rsplit(maxsplit=1)[0], [])

        matches = [f for f in options if f.startswith(text)]

        if not matches:
            search_path = self.buf.rsplit(maxsplit=1)[-1].replace("\x00", "")
            base_path = os.path.dirname(search_path)
            matches = sorted(os.path.relpath(p, base_path) + ("/" if os.path.isdir(p) else "") for p in glob.glob(search_path + "*"))

        return matches[state] if state < len(matches) else None

completer = PyShellCompleter()

def enable():
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")


import importlib, pkgutil
__all__ = [module.name for module in pkgutil.iter_modules(__path__)]
for module in __all__:
    completer.register(importlib.import_module(f"{__name__}.{module}").entries)