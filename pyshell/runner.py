import copy
import glob
import io
import os
import re
import shlex
import shutil
import sys
import subprocess
import traceback

from pyshell import pyshenv, commands, logger
from pyshell.utils.termcolors import fg as color

log = logger.logger(__name__)


def run(inpt: str | list[str], capture_output=False):
    input_str = inpt if type(inpt) is str else " ".join(inpt)
    log.debug(f"input string: {input_str}")

    if "\n" in input_str:
        tokens = ""
        log.debug("newline detected, treating as python statement")
        pipeline = [(["^"], input_str, sys.stdin, sys.stdout, sys.stderr)]
    else:
        tokens = tokenize(input_str)
        log.debug(f"parsed tokens: {tokens}")
        pipeline = parse(tokens)
    log.debug(f"parsed pipeline: {pipeline}")

    status = 0

    for i, (command, command_str, stdin, stdout, stderr) in enumerate(pipeline):
        if i > 0 and stdin == sys.stdin:
            stdin = process.stdout
        if i + 1 < len(pipeline) and stdout == sys.stdout:
            stdout = subprocess.PIPE
        if capture_output and i + 1 == len(pipeline):
            stdout = subprocess.PIPE

        status, process = execute(command, command_str, stdin, stdout, stderr)
        if status != 0:
            break

    if capture_output:
        output = (process.stdout if status == 0 else process.stderr).read().decode()
    return status if not capture_output else (status, output)


def tokenize(input_str: str):
    toks = []
    current = ""
    end = ""

    i = 0
    while i < len(input_str):
        match input_str[i]:
            case c if end and c == end:
                current += c
                end = ""
            case c if end:
                current += c
            case '"' | "'":
                current += c
                end = c
            case "$" if input_str[i:i + 2] == "$(":
                current += "$("
                end = ")"
                i += 1
            case "|", "<", ">":
                if current:
                    toks += [current]
                    current = ""
                
                if input_str[i:i + 2] == ">>":
                    toks += [">>"]
                    i += 1 
                else:
                    toks += [c]
            case c if c.isspace():
                if current:
                    toks += [current]
                    current = ""
            case _:
                current += c
        i += 1

    toks += [current]
    return toks


def parse(toks: list[str]):
    pipeline = []

    i = 0
    while i < len(toks):
        if i == 0:
            command_str = ""
            r, w, e = sys.stdin, sys.stdout, sys.stderr

            if toks[0] in pyshenv.aliases:
                aliases = copy.deepcopy(pyshenv.aliases)
                while cmd := aliases.pop(toks[0], None):
                    log.debug(f"resolving alias: {toks[0]} -> {cmd}")
                    toks[:1] = tokenize(cmd)

        match toks[i]:
            case t if t.startswith("#"):
                break
            case "|":
                command = toks[:i]
                pipeline += [(command, command_str, r, w, e)]
                toks = toks[i + 1:]
                i = -1
            case ">" | ">>":
                command = toks[:i]

                end = toks.index("|") if "|" in toks[i:] else len(toks)
                if "<" in toks[i:end]:
                    j = toks.index("<")
                    file = " ".join(toks[i + 1:j])
                    w = open(os.path.expanduser(os.path.expandvars(file)), "w" if t == ">" else "a")
                    file = " ".join(toks[j + 1:end])
                    r = open(os.path.expanduser(os.path.expandvars(file)), "r")
                else:
                    file = " ".join(toks[i + 1:end])
                    w = open(os.path.expanduser(os.path.expandvars(file)), "w" if t == ">" else "a")

                pipeline += [(command, command_str, r, w, e)]
                toks = toks[end + 1:]
                i = -1
            case "<":
                command = toks[:i]

                end = toks.index("|") if "|" in toks[i:] else len(toks)
                if ">" in toks[i:end] or ">>" in toks[i:end]:
                    j = toks.index(">") if ">" in toks[i:end] else toks.index(">>")
                    file = " ".join(toks[i + 1:j])
                    r = open(os.path.expanduser(os.path.expandvars(file)), "r")
                    file = " ".join(toks[j + 1:end])
                    w = open(os.path.expanduser(os.path.expandvars(file)), "w" if toks[j] == ">" else "a")
                else:
                    file = " ".join(toks[i + 1:end])
                    r = open(os.path.expanduser(os.path.expandvars(file)), "r")

                pipeline += [(command, command_str, r, w, e)]
                toks = toks[end + 1:]
                i = -1
            case command if command.startswith("$(") and command.endswith(")"):
                try:
                    status, output = run(command[2:-1], capture_output=True)
                    if status != 0:
                        raise Exception()

                    toks[i] = output.strip()
                    command_str += toks[i] + " "
                    i -= 1
                except Exception as e:
                    log.error("command substitution failed")
                    log.exception(e)
                    print(f"{color.red}Command substitution failed: {e}{color.reset}")
                    print(f"{color.red}{output}{color.reset}")
            case string if string and string[0] in ('"', "'") and string[0] == string[-1]:
                command_str += string + " "
                if toks[0] != "alias":
                    if string[0] == '"':
                        expanded = glob.glob(os.path.expanduser(os.path.expandvars(string[1:-1])))
                        toks[i:i+1] = expanded
                    else:
                        toks[i] = string[1:-1]
            case g if "*" in g or "?" in g:
                command_str += g + " "
                if toks[0] != "alias":
                    expanded = glob.glob(os.path.expanduser(os.path.expandvars(g)))
                    toks[i:i + 1] = expanded
                i += len(expanded) - 1
            case t:
                command_str += t + " "
                toks[i] = os.path.expanduser(os.path.expandvars(t))
        i += 1
    else:
        if toks:
            command = toks[:i]
            pipeline += [(command, command_str, sys.stdin, sys.stdout, sys.stderr)]

    return pipeline


def execute(command, command_str, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    try:
        status = 0
        proc = None

        match command[0]:
            case "":
                return
            case "import":
                try:
                    exec("import " + " ".join(command[1:]), pyshenv.namespace, pyshenv.namespace)
                except ModuleNotFoundError as e:
                    suggestion = traceback.format_exception(e)[-1].strip()
                    print(f"{color.red}{suggestion}{color.reset}")
                    status = 1
            case _ if command[0] in commands.__all__:
                log.debug(f"running built-in `{command[0]}` with args {command[1:]}")
                status = getattr(commands, command[0])(*command[1:]) or 0
            case _ if exe := shutil.which(command[0]):
                log.debug(f"spawning process {command[0]} ({exe})")
                status, proc = spawn_process(exe, command, stdin, stdout, stderr)
                log.debug(f"{command[0]} exited with status={status}")
            case _:
                log.debug(f"running as python code\n{command_str}")
                command_str = os.path.expandvars(command_str)
                command_str = re.sub(r"\$\((.*)\)", r"pyshell.runner.run(\1)", command_str)

                expression = True
                try:
                    log.debug(f"compiling as expression")
                    code = compile(command_str, "<string>", "eval")
                except SyntaxError:
                    expression = False
                    log.debug("failed")
                    try:
                        log.debug(f"compiling code as statement")
                        code = compile(command_str, "<string>", "exec")
                    except SyntaxError as e:
                        log.error(f"failed")
                        log.exception(e)
                        code = None
                        status = 1

                if code:
                    try:
                        func = eval if expression else exec
                        log.debug(f"running as {'eval' if expression else 'exec'}\n{command_str}")
                        if (res := func(command_str, pyshenv.namespace, pyshenv.namespace)) is not None:
                            print(res) 
                        log.debug(f"ok{f"\n{res}" if expression else ""}")
                        status = 0
                    except Exception as e:
                        log.error(f"error during {'eval' if expression else 'exec'}")
                        log.exception(e)
                        suggestion = traceback.format_exception(e)[-1].strip()
                        print(f"{color.red}{suggestion}{color.reset}")
                        status = 1
    except KeyboardInterrupt:
        print()
    
    return (status, proc)


def spawn_process(exe, command, stdin, stdout, stderr):
    proc = subprocess.Popen(
        command,
        executable=exe,
        preexec_fn=lambda: os.setpgid(os.getpid(), os.getpid()),
        cwd=os.getcwd(),
        env=os.environ.copy(),
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )

    pyshenv.add_job(proc)
    status = commands.fg()

    return status, proc
