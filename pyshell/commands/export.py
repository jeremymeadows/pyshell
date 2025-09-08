import argparse
import os
import re
import textwrap

from pyshell import pyshenv


#                        ( var )   =  ( "value"                  | 'value'                  | value )
pattern = re.compile(r'''(\w+)(?: ?= ?("(?:(?:[^"\\]*(?:\\.)?)*)"|'(?:(?:[^'\\]*(?:\\.)?)*)'|\S+))?''')

def _export(*args):
    parser = argparse.ArgumentParser(
        prog="export",
        description="Export a variable to the environment.",
        formatter_class = argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent('''\
            examples:
                # quotes are optional unless the value contains spaces
                export VAR = foo
                export VAR = $HOME/foo
                export VAR = "foo bar"
                export VAR = "$HOME/foo bar"

                # single quotes prevent variable expansion
                export VAR = '$NOT_EXPANDED'

                # export a variable from the shell environment
                var = "hello".upper()
                export var
                # var == $var == "HELLO"

                # non-string values keep their type in Python, but will become strings in the environment
                num = 42
                export num
                # num == 42, $num == "42"
            '''
        ),
    )
    parser.add_argument("variable", type=str, help="variable to export by name or in the form `name=value`")

    args = re.fullmatch(pattern, " ".join(args))
    if args:
        name, value = args.groups()
    else:
        try:
            parser.parse_args(["--help"])
        except SystemExit:
            return

    if value:
        if value.startswith('"'):
            value = os.path.expanduser(os.path.expandvars(value[1:-1]))
        elif value.startswith("'"):
            value = value[1:-1]
        os.environ[name] = value
    else:
        os.environ[name] = str(pyshenv.namespace[name])