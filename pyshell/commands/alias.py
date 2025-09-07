import argparse
import re
import shlex

from pyshell import pyshenv


def _alias(*args):
    parser = argparse.ArgumentParser(prog="alias", description="Create or display command aliases.")
    # parser.register('type', 'alias', lambda s: re.match(".* ?= ?[\"'].*[\"']"))
    parser.register('type', 'alias', lambda s: s==s)
    parser.add_argument("alias", type="alias", nargs="?", help="alias definitions in the form `name='value'`")

    try:
        _ = parser.parse_args(["foo"])
    except SystemExit:
        return

    if not args:
        for name, value in pyshenv.aliases.items():
            print(f"alias {name}=\"{value}\"")
    else:
        args = " ".join(args).strip()
        if "=" not in args:
            print("alias: invalid alias definition. Use the form name='value'")
            return

        alias, command = map(str.strip, args.split("=", 1))
        if any(c.isspace() for c in alias):
            print("alias: alias name cannot contain spaces")
            return
        pyshenv.aliases[alias] = command.strip('"').strip("'")