import copy
import glob
import io
import os
import shlex
import shutil
import signal
import sys
import subprocess
import termios
import traceback

from pyshell import pyshenv, commands, logger
from pyshell.utils.termcolors import fg as color

log = logger.logger(__name__)


class Command:
    def __init__(self, command, args, input_str, *, ins=sys.stdin, out=sys.stdout, err=sys.stderr):
        self.command = command
        self.args = args
        self.input_str = input_str
        self.ins = ins
        self.out = out
        self.err = err
    
    def __repr__(self):
        return "\n".join([f"Command<{self.command} [{" ".join(self.args)}]",
                f"\tstr: {self.input_str}",
                f"\tin: {self.ins.name}",
                f"\tout: {self.out.name if self.out != -1 else "PIPE"}",
            ">"])


def tokenize(input_str):
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


def parse(input_str):
    if "\n" in input_str:
        return [Command("^", [], input_str)]

    toks = tokenize(input_str)
    pipeline = []

    i = 0
    while i < len(toks):
        if i == 0:
            input_str = ""
            r, w, e = sys.stdin, sys.stdout, sys.stderr

        match toks[i]:
            case t if t.startswith("#"):
                break
            case "|":
                command, args = toks[0], toks[1:i]
                pipeline += [Command(command, args, input_str, ins=r, out=w, err=e)]
                toks = toks[i + 1:]
                i = -1
            case ">" | ">>":
                command, args = toks[0], toks[1:i]

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

                pipeline += [Command(command, args, input_str, ins=r, out=w, err=e)]
                toks = toks[end + 1:]
                i = -1
            case "<":
                command, args = toks[0], toks[1:i]

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

                pipeline += [Command(command, args, input_str, ins=r, out=w, err=e)]
                toks = toks[end + 1:]
                i = -1
            case command if command.startswith("$(") and command.endswith(")"):
                try:
                    proc = subprocess.run([sys.executable, "-P", "-m", "pyshell", "-c", command[2:-1]], capture_output=True, text=True)
                    if proc.returncode != 0:
                        raise Exception()

                    toks[i] = proc.stdout.strip()
                    input_str += toks[i] + " "
                    i -= 1
                except Exception as e:
                    print(f"{color.red}Command substitution failed: {e}{color.reset}")
                    print(f"{color.red}{proc.stderr}{color.reset}")
            case string if string and string[0] in ('"', "'") and string[0] == string[-1]:
                input_str += string + " "
                toks[i] = string[1:-1]
            case g if "*" in g or "?" in g:
                input_str += g + " "
                expanded = glob.glob(os.path.expanduser(os.path.expandvars(g)))
                toks[i:i + 1] = expanded
                i += len(expanded) - 1
            case t:
                input_str += t + " "
                toks[i] = os.path.expanduser(os.path.expandvars(t))
        i += 1
    else:
        if toks:
            command, args = toks[0], toks[1:i]
            pipeline += [Command(command, args, input_str)]

    return pipeline


def run_pipeline(pipeline):
    status = 0
    for i, command in enumerate(pipeline):
        if i > 0 and command.ins == sys.stdin:
            command.ins = process.stdout
        if i + 1 < len(pipeline) and command.out == sys.stdout:
            command.out = subprocess.PIPE

        status, process = run(command)
        if status != 0:
            return status
    return status


def resolve_alias(command: Command):
    aliases = copy.deepcopy(pyshenv.aliases)
    while cmd := aliases.pop(command.command, None):
        log.debug(f"resolving alias: {command.command} -> {cmd}")
        parts = shlex.split(cmd, posix=False)
        command.command = parts[0]
        command.args = parts[1:] + command.args
    return command


def spawn_process(command, exe):
    old_pgrp = os.tcgetpgrp(sys.stdin.fileno())
    old_attr = termios.tcgetattr(sys.stdin.fileno())

    try:
        proc = subprocess.Popen(
            [command.command, *command.args],
            executable=exe,
            preexec_fn=lambda: os.setpgid(os.getpid(), os.getpid()),
            cwd=os.getcwd(),
            env=os.environ.copy(),
            stdin=command.ins,
            stdout=command.out,
        )

        # set the child's process group as new foreground
        os.tcsetpgrp(sys.stdin.fileno(), proc.pid)
        # revive the child in case it was stopped before it was made foreground
        os.kill(proc.pid, signal.SIGCONT)

        status = proc.wait()

    finally:
        # ignore signals from changing tty
        old_hdlr = signal.signal(signal.SIGTTOU, signal.SIG_IGN)
        # make parent group foreground again
        os.tcsetpgrp(sys.stdin.fileno(), old_pgrp)
        # restore the handler
        signal.signal(signal.SIGTTOU, old_hdlr)
        # restore terminal attributes
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_attr)

    return status, proc


def run(command: Command):
    try:
        status = 0
        proc = None

        command = resolve_alias(command)

        match command.command:
            case "":
                return
            case "import":
                try:
                    exec("import " + " ".join(command.args), pyshenv.namespace, pyshenv.namespace)
                except ModuleNotFoundError as e:
                    suggestion = traceback.format_exception(e)[-1].strip()
                    print(f"{color.red}{suggestion}{color.reset}")
                    status = 1
            case _ if command.command in commands.__all__:
                log.debug(f"running built-in `{command.command}` with args {command.args}")
                status = getattr(commands, command.command)(pyshenv, *command.args) or 0
            case _ if exe := shutil.which(command.command):
                log.debug(f"spawning process {command.command} ({exe})")
                status, proc = spawn_process(command, exe)
                log.debug(f"{command.command} exited with status={status}")
            case _:
                expression = True
                log.debug(f"running as python code\n{command.input_str}")
                try:
                    log.debug(f"compiling as expression")
                    code = compile(command.input_str, "<string>", "eval")
                except SyntaxError:
                    expression = False
                    log.debug("failed")
                    try:
                        log.debug(f"compiling code as statement")
                        code = compile(command.input_str, "<string>", "exec")
                    except SyntaxError as e:
                        log.error(f"failed")
                        log.exception(e)
                        code = None
                        status = 1

                if code:
                    try:
                        func = eval if expression else exec
                        log.debug(f"running as {'eval' if expression else 'exec'}\n{command.input_str}")
                        if (res := func(command.input_str, pyshenv.namespace, pyshenv.namespace)) is not None:
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