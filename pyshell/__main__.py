import argparse
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
    parser.add_argument("-n", "--noexit", action="store_true", help="do not exit after running a command or script file")
    parser.add_argument("-f", "--config", type=str, help="path to config file")
    parser.add_argument("-e", "--env", type=str, nargs="+", help="set environment variables (KEY=VALUE)")
    parser.add_argument("-c", "--command", type=str, nargs="+", help="run a single command and exit")
    parser.add_argument("file", type=str, nargs="*", help="run a PyShell script file and exit")

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
            commands.source(pyshenv, args.config)
            for k, v in pyshenv.namespace.items():
                globals()[k] = v
        else:
            print(f"{color.red}Config file not found: {args.config}{color.reset}")
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

    out = sys.stdout

    for i, t in enumerate(toks[1:]):
        # print(t)
        match t:
            case _ if t.startswith("#"):
                break
            # case _ if t.startswith("$(") and t.endswith(")"):
            #     try:
            #         t = subprocess.check_output(t[2:-1], shell=True, text=True).strip()
            #     except subprocess.CalledProcessError as e:
            #         print(f"{color.red}Command substitution failed: {e}{color.reset}")

            case ">" | ">>":
                out = open(os.path.expanduser(os.path.expandvars(toks[i + 2])), "w" if t == ">" else "a")
                args.append(t[1:i + 1])
                break
            case "|":
                pass
            case _ if not (t[0] in ('"', "'") and t[0] == t[-1]):
                if "*" in t or "?" in t:
                    args += glob.glob(os.path.expanduser(os.path.expandvars(t)))
                else:
                    args += [os.path.expanduser(os.path.expandvars(t))]
            case _:
                args.append(t[1:-1])

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
                staus = run(" ".join([*shlex.split(pyshenv.aliases[command], posix=False), *args]))
            case _ if command in commands.__all__:
                status = getattr(commands, command)(pyshenv, *args) or 0
            case _ if shutil.which(command):
                proc = subprocess.run(
                    [sys.executable, "-m", "pyshell", "-c", "exec", input_str],
                    cwd=os.path.dirname(sys.argv[0]),
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
                    if (res := func(input_str, pyshenv.namespace, pyshenv.namespace)) is not None:
                        print(res) 
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