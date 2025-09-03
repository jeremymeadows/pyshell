import time

# thi is mostly here to simulate long-running commands
def _wait(pyshenv, s):
    time.sleep(int(s))