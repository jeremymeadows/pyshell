import argparse
import time
import os

from pyshell.logger import logfile


def _logs(*args):
    parser = argparse.ArgumentParser( prog="logs", description="Follow the PyShell log file")

    try:
        args = parser.parse_args(args)
    except SystemExit:
        return

    if not os.path.exists(logfile):
        print(f"No log file found at {logfile}.")
        return

    print(f"Following logs from {logfile}.\nPress Ctrl+C to stop.")

    try:
        with open(logfile, "r") as f:
            f.seek(0, os.SEEK_END)
            inode = os.fstat(f.fileno()).st_ino

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    while not (exists := os.path.exists(logfile)) or (i := os.stat(logfile).st_ino) != inode:
                        if exists:
                            inode = i
                            f.close()
                            f = open(logfile, "r")
                            break
                    continue
                print(line, end="")
    except KeyboardInterrupt:
        pass