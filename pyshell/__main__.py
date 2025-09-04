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

from pyshell import pyshenv, prompt, commands
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
            commands.source(pyshenv, file)
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
        run(" ".join(args.command))

    if args.repl:
        pyshenv.repl = True

    if pyshenv.repl:
        repl()


def repl():
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

        sys.__stdout__ = sys.stdout
        run(input_str)


@staticmethod
def run(input_str, out=sys.stdout, err=sys.stderr):
    toks = shlex.split(input_str, posix=False)
    command, args = toks[0], []

    for i, t in enumerate(toks):
        if i == 0:
            continue

        match t:
            case _ if t.startswith("#"):
                break
            case ">" | ">>":
                out = open(os.path.expanduser(os.path.expandvars(toks[i + 1])), "w" if t == ">" else "a")
                input_str = input_str.rstrip(" ".join(toks[i:]))
                break
            case _ if t.startswith("$(") and t.endswith(")"):
                try:
                    capture = io.StringIO()
                    run(t[2:-1], out=capture)
                    capture.seek(0)
                    t = capture.read().strip()
                    args += [os.path.expanduser(os.path.expandvars(t))]
                except Exception as e:
                    print(f"{color.red}Command substitution failed: {e}{color.reset}")
            case "|":
                pass
            case _ if t[0] in ('"', "'") and t[0] == t[-1]:
                args.append(t[1:-1])
            case _:
                if "*" in t or "?" in t:
                    args += glob.glob(os.path.expanduser(os.path.expandvars(t)))
                else:
                    args += [os.path.expanduser(os.path.expandvars(t))]

    try:
        status = 0
        match command:
            case "":
                return
            case "help":
                parser.print_help()
            case "import":
                exec("import " + " ".join(args), pyshenv.namespace, pyshenv.namespace)
            case _ if command in pyshenv.aliases:
                cmd = pyshenv.aliases.pop(command)
                status = run(" ".join([*shlex.split(cmd, posix=False), *args]))
                pyshenv.aliases[command] = cmd
            case _ if command in commands.__all__:
                status = getattr(commands, command)(pyshenv, *args) or 0
            case _ if shutil.which(command):
                proc = subprocess.run(
                    [sys.executable, "-m", "pyshell", "-c", "exec", " ".join([command, *args])],
                    cwd=os.getcwd(),
                    env=os.environ.copy(),
                    stdout=out,
                )
                status = proc.returncode
            case _:
                expression = True
                try:
                    code = compile(input_str, "<string>", "eval")
                except SyntaxError:
                    expression = False
                    try:
                        code = compile(input_str, "<string>", "exec")
                    except SyntaxError as e:
                        pass

                try:
                    func = eval if expression else exec
                    sys.stdout = out

                    if (res := func(input_str, pyshenv.namespace, pyshenv.namespace)) is not None:
                        print(res, file=out) 
                    
                    sys.stdout = sys.__stdout__

                    for k, v in pyshenv.namespace.items():
                        if k in globals():
                            globals()[k] = v
                except Exception as e:
                    suggestion = traceback.format_exception(e)[-1].strip()
                    print(f"{color.red}{suggestion}{color.reset}")
                    status = 1
    except KeyboardInterrupt:
        print()
    
    os.environ["LAST_EXIT_CODE"] = str(status)
    return status


if __name__ == "__main__":
    pyshenv.run = run
    main()