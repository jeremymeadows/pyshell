import argparse
import glob
import io
import os
import re
import readline
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import traceback

import pyshell

from pyshell import pyshenv, commands, runner, complete, logger
from pyshell.utils.termcolors import fg as color

log = logger.logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        prog="pysh",
        description="A simple Python-based shell",
        epilog=f"PyShell {pyshell.__version__}",
        add_help=True,
    )

    # parser.add_argument("-h", "--help", action="store_true", help="show this help message and exit")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {pyshell.__version__}")
    parser.add_argument("-p", "--pure", action="store_true", help="run the shell without inheriting the environment variables")
    parser.add_argument("-i", "--interactive", action="store_true", help="run the shell in interactive mode even if stdin is not a terminal")
    parser.add_argument("-r", "--repl", action="store_true", help="enter the repl after running a command or script file")
    parser.add_argument("-f", "--config", type=str, help="path to config file")
    parser.add_argument("-e", "--env", type=str, nargs="+", help="set environment variables (KEY=VALUE)")
    parser.add_argument("-c", "--command", type=str, nargs="+", help="run a single command and exit")
    parser.add_argument("file", type=str, nargs="*", help="run a PyShell script file and exit")

    args = parser.parse_args()
    pyshenv.help = parser.format_help()

    if args.pure:
        env = { k: v for k, v in os.environ.items() if k in ("USER", "HOME", "TERM", "PATH", "EDITOR", "PAGER", "SHLVL", "DISPLAY") or k.startswith("PYTHON") }
        os.environ.clear()
        os.environ = env
    
    config = args.config or os.environ.get("CONFIG") or os.path.join(os.path.expanduser("~"), ".pyshrc")
    os.environ["CONFIG"] = config
    
    os.environ["PWD"] = os.getcwd()
    os.environ["OLDPWD"] = os.getcwd()
    
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
            commands.source(file)
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
        log.debug(f"running command from args: {args.command}")
        runner.run(" ".join(args.command))

    if args.repl:
        pyshenv.repl = True

    if pyshenv.repl:
        prompt = pyshenv.namespace["prompt"]
        complete.enable()

        signal.signal(signal.SIGTSTP, lambda *_: log.debug('ignore sigtstp'))
        exec("import pyshell", pyshenv.namespace)

        while True:
            prompt_str = prompt().format(**{ k: v() if callable(v) else v for k, v in pyshenv.prompt_subs.items() })

            try:
                input_str = input(prompt_str if pyshenv.interactive else "")
                readline.write_history_file(os.environ.get("HISTORY"))
            except KeyboardInterrupt:
                log.debug("sigint on repl")
                print(f"{color.red}^C{color.reset}")
                continue
            except EOFError:
                log.debug("exit on eof")
                if pyshenv.interactive:
                    print(f"{color.red}^D{color.reset}")
                elif pyshenv.repl:
                    sys.stdin = open("/dev/tty")
                    log.debug("switch to interactive mode")
                    pyshenv.interactive = True
                    continue
                sys.exit(0)

            if not input_str:
                continue

            status = runner.run(input_str)
            os.environ["LAST_EXIT_CODE"] = str(status)
            if status != 0:
                print("command failed: status code", status)


if __name__ == "__main__":
    log.debug(f"Starting PyShellv{pyshell.__version__}")
    try:
        main()
    except Exception as e:
        log.critical("uncaught exception")
        log.exception(e)
        sys.exit(1)
    finally:
        os.environ["SHLVL"] = str(int(os.environ.get("SHLVL", 1)) - 1)
        log.debug("exiting pysh")