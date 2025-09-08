import argparse
import re
import shlex
import textwrap

from pyshell import pyshenv

#                         ( name ) =  ( "value"                  | 'value'                  | value )
pattern = re.compile(r'''(\S+)(?: ?= ?("(?:(?:[^"\\]*(?:\\.)?)*)"|'(?:(?:[^'\\]*(?:\\.)?)*)'|.*))''')

def _alias(*args):
    parser = argparse.ArgumentParser(
        prog="alias",
        description="Create or display command aliases.",
        formatter_class = argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent('''\
            examples:
                # quotes are optional except to preserve spaces
                alias .. = cd ..
                alias ll = ls -la
                alias projects = cd "~/Project Directory/"

                # remove an alias by setting it to an empty command
                alias foo = echo foo
                alias foo =
            '''
        ),
    )
    parser.add_argument("alias", type=str, help="alias definitions in the form `alias=command`")

    if not args:
        for alias, command in pyshenv.aliases.items():
            print(f"alias {alias} = {command}")
        return

    args = re.fullmatch(pattern, " ".join(args))
    if args:
        alias, command = args.groups()
    else:
        try:
            parser.parse_args(["--help"])
        except SystemExit:
            return
    
    if not command:
        del pyshenv.aliases[alias]
    else:
        pyshenv.aliases[alias] = command