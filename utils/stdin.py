import sys, tty, termios

KEYS = {
    "[A": "UP",
    "[B": "DOWN",
    "[C": "RIGHT",
    "[D": "LEFT",
    "[3": "DELETE",
    "[5": "PAGE_UP",
    "[6": "PAGE_DOWN",
    "[H": "HOME",
    "[F": "END",
}

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)

        if ch == "\x1b":  # ESC
            ch += sys.stdin.read(2)  # Read the next two characters
            if ch[1:] in KEYS:
                ch = KEYS[ch[1:]]
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch
