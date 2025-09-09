import builtins
import glob
import os
import readline

from pyshell import commands, logger

log = logger.logger(__name__)


class PyShellCompleter:
    def __init__(self):
        self._bins = []
        self._path = ""
        self.buf = ""
        self.prefixes = dict()
    
    @property
    def bins(self):
        # update binaries cache if path has changed
        if (PATH := os.getenv("PATH", "")) != self._path:
            self._path = PATH
            for path in self._path.split(os.pathsep):
                try:
                    for file in os.listdir(path):
                        if os.access(os.path.join(path, file), os.X_OK):
                            self._bins += [file]
                except FileNotFoundError:
                    pass
            self._bins = sorted(set(self._bins))
        return self._bins

    def register(self, entries):
        for prefix, options in entries.items():
            self.prefixes[prefix] = options

    def glob_search_path(self):
        search_path = os.path.expanduser(self.buf.rsplit(maxsplit=1)[-1].replace("\x00", ""))
        base_path = os.path.dirname(os.path.expanduser(search_path))
        matches = sorted(os.path.relpath(p, base_path) + ("/" if os.path.isdir(p) else "") for p in glob.glob(search_path + "*"))
        log.debug(matches)
        return matches

    def expand_match_path(self, path):
        search_path = os.path.expanduser(self.buf.rsplit(maxsplit=1)[-1].replace("\x00", ""))
        base_path = os.path.dirname(search_path)
        return os.path.join(base_path, path)

    def complete(self, text, state):
        # text is weird and truncates itself at symbols so use readline to parse full buffer manually
        if state == 0:
            self.buf = readline.get_line_buffer()
            if self.buf.endswith("~"):
                readline.insert_text("/")
                self.buf += "/"
            self.buf = self.buf.lstrip("exec ")
            if self.buf != self.buf.rstrip():
                self.buf += "\x00"

        if self.buf.startswith((".", "/", "~")) and " " not in self.buf:
            options = [m for m in self.glob_search_path() if (p := self.expand_match_path(m)) and os.path.isdir(p) or os.access(p, os.X_OK)]
        elif " " not in self.buf:
            options = self.bins + commands.__all__ + [b for b in dir(builtins) if b.islower()]
        else:
            options = self.prefixes.get(self.buf.rsplit(maxsplit=1)[0], [])

        matches = [f for f in options if f.startswith(text)]

        if not matches:
            matches = self.glob_search_path()

        return matches[state] if state < len(matches) else None

completer = PyShellCompleter()

def enable():
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")


import importlib, pkgutil
__all__ = [module.name for module in pkgutil.iter_modules(__path__)]
for module in __all__:
    importlib.import_module(f"{__name__}.{module}")