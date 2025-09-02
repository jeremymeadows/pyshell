import argparse
import os
import sys

def _exit(pyshenv, *args):
    parser = argparse.ArgumentParser(prog="exit", description="Exit the shell.")
    parser.add_argument("status", type=int, default=os.environ.get("LAST_EXIT_CODE", 0), nargs="?", help="the exit status (defaults to the status of the last executed command)")
    
    try:
        args = parser.parse_args(args)
    except SystemExit:
        return
    
    sys.exit(args.status)