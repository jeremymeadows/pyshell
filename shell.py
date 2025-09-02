import glob
import os
import re
import readline
import shlex
import shutil
import socket
import subprocess
import sys
import traceback

import commands

from utils.termcolors import colors
from utils.stdin import getch

@staticmethod
def prompt():
    uid_color = colors.fg.green if os.geteuid() != 0 else colors.fg.red
    cwd_color = colors.fg.blue if os.access(os.getcwd(), os.W_OK) else colors.fg.red
    return f"{uid_color}{{user}}{colors.fg.green}@{{host}} {cwd_color}{{cwd}}{colors.fg.white}\n> "

prompt_variables = {
    "user": os.getlogin(),
    "host": socket.gethostname(),
    "symbol": "",
}

aliases = {
    "..": "cd ..",
    "ll": "ls -l",
}

pyshenv = type("PyShellEnv", (object,), {
    "globals": dict(),
    "locals": dict(),
    "prompt": prompt,
    "run": lambda: None,
    "aliases": aliases,
    "interactive": sys.stdin.isatty(),
    "noexit": False,
})()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        # prog="PyShell",
        description="A simple Python-based shell",
        epilog="Still in development",
        add_help=True,
    )

    # parser.add_argument("-h", "--help", action="store_true", help="show this help message and exit")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.0.1")
    parser.add_argument("-p", "--pure", action="store_true", help="run the shell without inheriting the environment variables")
    parser.add_argument("-i", "--interactive", action="store_true", help="run the shell in interactive mode even if stdin is not a terminal")
    parser.add_argument("-e", "--env", type=str, nargs="+", help="set environment variables (KEY=VALUE)")
    parser.add_argument("-f", "--config", type=str, help="path to config file")
    parser.add_argument("-c", "--command", type=str, nargs="+", help="run a single command and exit")
    parser.add_argument("file", type=str, nargs="*", help="run a PyShell script file and exit")
    parser.add_argument("-n", "--noexit", action="store_true", help="do not exit after running a command or script file")

    args = parser.parse_args()
    sys.argv[0] = os.path.join(os.getcwd(), os.path.basename(sys.argv[0]))

    if args.pure:
        env = { k: v for k, v in os.environ.items() if k in ("USER", "HOME", "TERM", "PATH", "EDITOR", "PAGER", "SHLVL", "DISPLAY") }
        os.environ.clear()
        os.environ = env
    
    if args.interactive:
        pyshenv.interactive = True
    
    if args.noexit:
        pyshenv.noexit = True
    
    os.environ["CONFIG"] = os.path.join(os.path.expanduser("~"), ".pyshrc")
    
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

    if args.config:
        if os.path.isfile(args.config):
            with open(args.config, "r") as f:
                exec(f.read(), globals(), locals())
        else:
            print(f"{colors.fg.red}Config file not found: {args.config}{colors.fg.reset}")
            sys.exit(1)
    
    try:
        readline.read_history_file(os.environ.get("HISTORY"))
    except FileNotFoundError:
        open(os.environ.get("HISTORY"), "wb").close()

    if args.command:
        run(" ".join(args.command))
    else:
        repl()


def repl():
    while True:
        prompt_str = pyshenv.prompt().format(cwd=os.path.join(os.getcwd().replace(os.getenv("HOME", "~"), "~"), ""), **prompt_variables)

        try:
            input_str = input(prompt_str if pyshenv.interactive else "")
            readline.write_history_file(os.environ.get("HISTORY"))
        except KeyboardInterrupt:
            print(f"{colors.fg.red}^C{colors.fg.reset}")
            continue
        except EOFError:
            if pyshenv.interactive:
                print(f"{colors.fg.red}^D{colors.fg.reset}")
            elif pyshenv.noexit:
                sys.stdin = open("/dev/tty")
                pyshenv.interactive = True
                continue
            sys.exit(0)

        if not input_str:
            continue

        run(input_str)

@staticmethod
def run(input_str):
    toks = shlex.split(input_str, posix=False)
    command, args = toks[0], []

    for t in toks[1:]:
        if t.startswith("#"):
            break

        if not (t[0] in ('"', "'") and t[0] == t[-1]):
            if "*" in t or "?" in t:
                args += glob.glob(os.path.expanduser(os.path.expandvars(t)))
            else:
                args += [os.path.expanduser(os.path.expandvars(t))]
        else:
            args.append(t[1:-1])

    try:
        match command:
            case "":
                return
            case "help":
                parser.print_help()
            case "import":
                exec("import " + " ".join(args), pyshenv.globals, pyshenv.locals)
            case _ if command in aliases:
                run(" ".join([*shlex.split(aliases[command], posix=False), *args]))
            case _ if command in commands.__all__:
                getattr(commands, command)(pyshenv, *args)
            case _ if shutil.which(command):
                subprocess.run([sys.executable, sys.argv[0], "-c", "exec", input_str], env=os.environ.copy())
            case _:
                expression = True
                try:
                    code = compile(input_str, "<string>", "eval")
                except SyntaxError:
                    expression = False
                    code = compile(input_str, "<string>", "exec")
                
                try:
                    func = eval if expression else exec
                    if (res := func(input_str, pyshenv.globals, pyshenv.locals)) is not None:
                        print(res)
                except Exception as e:
                    suggestion = traceback.format_exception(e)[-1].strip()
                    print(f"{colors.fg.red}{suggestion}{colors.fg.reset}")
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    pyshenv.run = run
    main()