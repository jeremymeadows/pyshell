import argparse
import glob
import io
import os
import re
import readline
import shlex
import shutil
import socket
import subprocess
import sys
import traceback

from pyshell import pyshenv, runner
from pyshell.commands import source
from pyshell.utils.termcolors import fg as color

def main():
    parser = argparse.ArgumentParser(
        prog="pysh",
        description="A simple Python-based shell",
        epilog="Still in development",
        add_help=True,
    )

    # parser.add_argument("-h", "--help", action="store_true", help="show this help message and exit")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.0.1")
    parser.add_argument("-p", "--pure", action="store_true", help="run the shell without inheriting the environment variables")
    parser.add_argument("-i", "--interactive", action="store_true", help="run the shell in interactive mode even if stdin is not a terminal")
    parser.add_argument("-r", "--repl", action="store_true", help="enter the repl after running a command or script file")
    parser.add_argument("-f", "--config", type=str, help="path to config file")
    parser.add_argument("-e", "--env", type=str, nargs="+", help="set environment variables (KEY=VALUE)")
    parser.add_argument("-c", "--command", type=str, nargs="+", help="run a single command and exit")
    parser.add_argument("file", type=str, nargs="*", help="run a PyShell script file and exit")

    args = parser.parse_args()
    sys.argv[0] = os.path.join(os.getcwd(), os.path.basename(sys.argv[0]))

    if args.pure:
        env = { k: v for k, v in os.environ.items() if k in ("USER", "HOME", "TERM", "PATH", "EDITOR", "PAGER", "SHLVL", "DISPLAY") or k.startswith("PYTHON") }
        os.environ.clear()
        os.environ = env
    
    config = args.config or os.environ.get("CONFIG") or os.path.join(os.path.expanduser("~"), ".pyshrc")
    os.environ["CONFIG"] = config
    
    os.environ["PWD"] = os.getcwd()
    os.environ["OLDPWD"] = os.getcwd()
    
    os.environ["SHELL"] = sys.argv[0]
    os.environ["SHLVL"] = str(int(os.environ.get("SHLVL", "0")) + 1)

    os.environ["HISTORY"] = os.path.join(os.path.expanduser("~"), ".pyshell_history")

    os.environ["LAST_EXIT_CODE"] = "0"

    for var in args.env or []:
        if "=" in var:
            key, value = var.split("=", 1)
            env[key] = value

    if args.interactive:
        pyshenv.interactive = True

    if args.command or args.file:
        pyshenv.repl = False

    for file in [config, *args.file]:
        if os.path.isfile(file):
            source(pyshenv, file)
        elif file == config and not os.environ.get("CONFIG_WARN", ""):
            os.environ["CONFIG_WARN"] = "1"
            print(f"{color.yellow}Config file ({config}) was not found{color.reset}")
        elif file != config:
            print(f"{color.red}File not found: {file}{color.reset}")
            sys.exit(1)

    try:
        readline.read_history_file(os.environ.get("HISTORY"))
    except FileNotFoundError:
        open(os.environ.get("HISTORY"), "wb").close()

    if args.command:
        runner.run_pipeline(runner.parse(" ".join(args.command)))

    if args.repl:
        pyshenv.repl = True

    if pyshenv.repl:
        prompt = pyshenv.namespace["prompt"]

        while True:
            prompt_str = prompt().format(**{ k: v() if callable(v) else v for k, v in pyshenv.prompt_subs.items() })

            try:
                input_str = input(prompt_str if pyshenv.interactive else "")
                readline.write_history_file(os.environ.get("HISTORY"))
            except KeyboardInterrupt:
                print(f"{color.red}^C{color.reset}")
                continue
            except EOFError:
                if pyshenv.interactive:
                    print(f"{color.red}^D{color.reset}")
                elif pyshenv.repl:
                    sys.stdin = open("/dev/tty")
                    pyshenv.interactive = True
                    continue
                sys.exit(0)

            if not input_str:
                continue

            pipeline = runner.parse(input_str)
            status = runner.run_pipeline(pipeline)
            os.environ["LAST_EXIT_CODE"] = str(status)
            if status != 0:
                print("command failed: status code", status)


if __name__ == "__main__":
    main()