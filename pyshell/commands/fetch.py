import argparse
import os
import platform
import socket
import shutil
import subprocess
import sys

import pyshell
from pyshell.utils.termcolors import fg as color


funcs = {
  "user": os.getlogin,
  "host": platform.node,
  "distro": lambda: distro(),
  "shell": lambda: f"PyShell {pyshell.__version__}" if (sh := os.environ["SHELL"]) == "pysh" else sh,
  "terminal": lambda: os.environ["TERM"],
  "kernel": lambda: f"{platform.system()} {platform.release()}",
  "cpu": lambda: cpu(),
  "mem": lambda: mem(),
  "disk": lambda: disk(),
  "ip": lambda: ip(),
}

def _fetch(*args):
    parser = argparse.ArgumentParser(prog="fetch", description="Display system stats.")
    
    try:
        args = parser.parse_args(args)
    except SystemExit:
        return
    
    out = { name: f() for name, f in funcs.items()}
    size = (max(len(name) for name in out), max(len(val) for val in out.values()))

    colors = [color.red, color.green, color.yellow, color.blue, color.magenta, color.cyan]
    lines = []

    lines += ["╭─" + "─" * size[0] + "─┬─" + "─" * size[1] + "─╮"]
    for i, (name, val) in enumerate(out.items()):
        lines += [f"│ {colors[i % len(colors)]}{name:{size[0]}}{color.reset} │ {val:{size[1]}} │"]
    lines += [("╰─" + "─" * size[0] + "─┴─" + "─" * size[1] + "─╯")]

    lines += [" " + "".join(f"{c}███{color.reset}" for c in [color.black, *colors, color.white])]
    lines += [" " + "".join(f"{c}███{color.reset}" for c in [color.grey, *colors, color.light_white])]

    if os.get_terminal_size().columns >= len(lines[0]) + 25:
        proc = subprocess.run("kitten icat --detect-support".split(), capture_output=True)
        if proc.returncode == 0:
            # 12 lines at 12pt font
            proc = subprocess.run("kitten icat --use-window-size 25,12,252,252 --align left".split() + [sys.path[0] + "/pie_shell.png"])
        if proc.returncode == 0:
            lines = ["\033[F" * 14] + [" " * 25 + line for line in lines]

    print("\n".join(lines))

def distro():
    f = open("/etc/os-release").readlines()
    d = ""
    for line in f:
        if line.startswith("PRETTY_NAME"):
            d = line.split("=")[-1].strip().strip('"')
            break
    return d

def cpu():
    f = open("/proc/cpuinfo").readlines()
    data = {k: v.strip() for k, v in (line.split(":") for line in open("/proc/meminfo").readlines())}
    model = ""
    count = 0
    for line in f:
        if line.startswith("model name"):
            model = line.split(":")[-1].strip()
            count += 1
    return model

def mem():
    data = {k: v.strip() for k, v in (line.split(":") for line in open("/proc/meminfo").readlines())}

    exp = 2**20
    total = int(data["MemTotal"].split()[0]) / exp
    free = int(data["MemFree"].split()[0]) / exp
    avail = int(data["MemAvailable"].split()[0]) / exp
    return f"{total - avail:.1f} / {total:.1f} GB Used ({(total - avail) / total * 100:.1f}%)"

def disk():
    parts = ["/", "/home"]
    total, used, free = 0, 0, 0
    for p in parts:
        u = shutil.disk_usage(p)
        total += u.total
        used += u.used
        free += u.free
    # exp = 2**30
    exp = 1e9
    return f"{used / exp:.1f} GB / {total / exp:.1f} GB Used ({free / exp:.1f} GB Free)"

def ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("0.0.0.1", 0))
    return s.getsockname()[0]