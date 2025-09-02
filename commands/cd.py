import argparse
import os

def _cd(pyshenv, *args):
    parser = argparse.ArgumentParser(prog="cd", description="Change the shell working directory.")
    parser.add_argument("path", nargs="*", help="the path to change to")
    args = parser.parse_args(args)

    path = " ".join(args.path)
    if not path:
        path = os.environ.get("HOME", os.getcwd())
    elif path == "-":
        path = os.getenv("OLDPWD", os.getcwd())

    try:
        os.chdir(path)
    except FileNotFoundError:
        print(f"cd: no such file or directory: {path}")
        return

    os.environ["OLDPWD"] = os.getenv("PWD", "")
    os.environ["PWD"] = os.getcwd()