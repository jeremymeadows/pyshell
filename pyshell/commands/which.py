import argparse
import shutil
import sys

from pyshell import pyshenv, commands


def _which(*args):
    parser = argparse.ArgumentParser(prog="which", description="Print the full path of commands found in the system PATH.")
    parser.add_argument("commands", nargs="+", help="the command to find")

    try:
        args = parser.parse_args(args)
    except SystemExit:
        return
    
    for cmd in args.commands:
        if cmd in pyshenv.aliases:
            print("alias", cmd)
        elif cmd in commands.__all__:
            print("builtin", cmd)
        elif path := shutil.which(cmd):
            print(path)
        else:
            print(f"no {cmd} in PATH", file=sys.stderr)