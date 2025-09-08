import os
import glob
import readline

from pyshell import logger

log = logger.logger(__name__)


class PyShellCompleter:
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

    def glob_search_path(self):
        search_path = self.buf.rsplit(maxsplit=1)[-1].replace("\x00", "")
        base_path = os.path.dirname(search_path)
        matches = sorted(os.path.relpath(p, base_path) + ("/" if os.path.isdir(p) else "") for p in glob.glob(search_path + "*"))
        log.debug(matches)
        return matches

    def expand_match_path(self, path):
        search_path = self.buf.rsplit(maxsplit=1)[-1].replace("\x00", "")
        base_path = os.path.dirname(search_path)
        return os.path.join(base_path, path)

    def complete(self, text, state):
        # text is weird an truncates itself at symbols so use readline to parse full buffer manually
        if state == 0:
            self.buf = os.path.expanduser(readline.get_line_buffer())
            self.buf = self.buf.lstrip("exec ")
            if self.buf != self.buf.rstrip():
                self.buf += "\x00"

        if self.buf.startswith((".", "/", "~")) and " " not in self.buf:
            matches = [m for m in self.glob_search_path() if os.path.isdir(self.expand_match_path(m)) or os.access(self.expand_match_path(m), os.X_OK)]
            return matches[state] if state < len(matches) else None
        elif " " not in self.buf:
            options = self.bins
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