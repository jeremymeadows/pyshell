import argparse
import os
import subprocess
import shlex
import shutil


def _exec(pyshenv, *args):
    parser = argparse.ArgumentParser(prog="exec", description="Replace the shell with the given command.")
    parser.add_argument("command", help="the command to execute with its arguments")
    parser.add_argument("args", nargs="*", help="arguments for the command")
    
    if args and args[0] in ("--help", "-h"):
        parser.print_help()
        return
    
    if path := shutil.which(args[0]):
        os.execv(path, args)