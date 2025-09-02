import argparse
import re
import shlex

def _alias(pyshenv, *args):
    parser = argparse.ArgumentParser(prog="alias", description="Create or display command aliases.")
    # parser.register('type', 'alias', lambda s: re.match(".* ?= ?[\"'].*[\"']"))
    parser.register('type', 'alias', lambda s: s==s)
    parser.add_argument("alias", type="alias", nargs="?", help="alias definitions in the form `name='value'`")

    try:
        _ = parser.parse_args(["foo"])
    except SystemExit:
        return

    if len(args) > 0:
        args = " ".join(args).strip()
        if "=" not in args:
            print("alias: invalid alias definition. Use the form name='value'")
            return
        alias, command = args.split("=", 1)
        pyshenv.aliases[alias.strip()] = command.strip().strip('"').strip("'")
    else:
        for name, value in pyshenv.aliases.items():
            print(f"alias {name}=\"{value}\"")