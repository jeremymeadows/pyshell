import argparse
import os
import subprocess

def exec(pyshenv, *args):
    parser = argparse.ArgumentParser(prog="exec", description="Replace the shell with the given command.")
    parser.add_argument("command", help="the command to execute with its arguments")
    parser.add_argument("args", nargs="*", help="arguments for the command")
    
    if args and args[0] in ("--help", "-h"):
        parser.print_help()
        return
    
    command, args = (args[0], " ".join(args[1:]) if len(args) > 1 else None)

    os.execvpe(command, [command] + (shlex.split(args) if args else []), env=os.environ.copy())