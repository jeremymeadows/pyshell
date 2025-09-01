import os
import socket
import subprocess
import shutil
import sys
import traceback

import readline

import commands

from utils.termcolors import colors
from utils.stdin import getch

def prompt():
    uid_color = colors.fg.green if os.geteuid() != 0 else colors.fg.red
    cwd_color = colors.fg.blue if os.access(os.getcwd(), os.W_OK) else colors.fg.red
    return f"{uid_color}{{user}}{colors.fg.green}@{{host}} {cwd_color}{{cwd}}{colors.fg.white}\n> "

prompt_variables = {
    "user": os.getlogin(),
    "host": socket.gethostname(),
    "symbol": "",
}

# from config import prompt

aliases = dict()

env = os.environ.copy()

history = []
hist_ndx = -1


while True:
    prompt_str = prompt().format(cwd=os.getcwd().replace(os.getenv("HOME"), "~") + "/", **prompt_variables)
    # print(prompt_str, end="", flush=True)

    try:
        input_str = input(prompt_str)
    except KeyboardInterrupt:
        print(f"{colors.fg.red}^C{colors.fg.reset}")
        continue
    except EOFError:
        print(f"{colors.fg.red}^D{colors.fg.reset}")
        sys.exit(0)
    # cursor = -1

    # while (ch := getch()) != "\r":
    #     match ch:
    #         case "\x03": # Ctrl-C
    #             buffer = []
    #             print(f"{colors.fg.red}^C{colors.fg.reset}", end="", flush=True)
    #             break
    #         case "\x04": # Ctrl-D
    #             print(f"{colors.fg.red}^D{colors.fg.reset}", end="", flush=True)
    #             sys.exit(0)
    #         case "\x7f": # Backspace
    #             if cursor > 0:
    #                 buffer.pop(cursor - 1)
    #                 cursor -= 1
    #                 # redraw line
    #                 sys.stdout.write("\r" + prompt_str + "".join(buffer) + " ")
    #                 sys.stdout.write("\r" + prompt_str + "".join(buffer[:cursor]))
    #                 sys.stdout.flush()
    #         case "\x1b": # ESC
    #             pass
    #         case "UP":
    #             ch = ""
    #         case "DOWN":
    #             ch = ""
    #         case "LEFT":
    #             if cursor > 0:
    #                 cursor -= 1
    #                 print("\b", end="", flush=True)
    #         case "RIGHT":
    #             if cursor < len(buffer):
    #                 print(buffer[cursor], end="", flush=True)
    #                 cursor += 1
    #         case _:
    #             buffer.insert(cursor, ch)
    #             cursor += 1
    #             # redraw line
    #             sys.stdout.write("\r" + prompt_str + "".join(buffer) + " ")
    #             sys.stdout.write("\r" + prompt_str + "".join(buffer[:cursor]))
    #             sys.stdout.flush()
    #             #input_str += ch
    #             #pos += 1
    #             #print(input_str[pos:], end="", flush=True)
    # print()

    if not input_str:
        continuereadline

    # input_str = "".join(buffer).strip()

    # history += [input_str]
    # hist_ndx = len(history) - 1
    command, args = (input_str.split(" ", 1) + [None])[:2]

# def run(command, *args):
    match command:
        case "":
            continue
        case _ if command in aliases:
            command, *args = (aliases[command].split(" ") + (args.split(" ") if args else []))[:2]
        case _ if command in commands.__all__:
            getattr(commands, command)(*(args.split() if args else []))
        case "exit":
            sys.exit(0)
        # case "help":
        #     if args:
        #         try:
        #             print(getattr(commands, args).__doc__)
        #         except Exception as e:
        #             print(f"Command not found: {args}")
        #     else:
        #         print("Available commands:")
        #         print(", ".join(commands.__all__))
        # case "alias":
        #     if args:
        #         if "=" in args:
        #             name, value = args.split("=", 1)
        #             aliases[name.strip()] = value.strip().strip('"').strip("'")
        #         else:
        #             for name, value in aliases.items():
        #                 print(f"{name}='{value}'")
        #     else:
        #         for name, value in aliases.items():
        #             print(f"{name}='{value}'")
        case _ if shutil.which(command):
            subprocess.run([command] + (args.split() if args else []), env=env)
        case _:
            try:
                res = eval(input_str, globals(), locals())
                print(res)
            except Exception as e:
                suggestion = traceback.format_exception(e)[-1].strip()
                print(f"{colors.fg.red}{suggestion}{colors.fg.reset}")