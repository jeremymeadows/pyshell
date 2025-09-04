import argparse
import os


def _umask(pyshenv, *args):
    parser = argparse.ArgumentParser(prog="umask", description="Set or display the file mode creation mask.")
    parser.add_argument("-o", "--octal", action="store_true", help="display the umask in octal format")
    parser.add_argument("mode", type=str, nargs="?", help="the new file mode creation mask (in octal)")

    try:
        args = parser.parse_args(args)
    except SystemExit:
        return

    if not args.mode:
        mask = os.umask(0)
        os.umask(mask)

        if args.octal:
            print(f"{mask:04o}")
        else:
            print(format_umask_str(mask))
            
    else:
        try:
            mode = int(args.mode, 8)

            if mode < 0 or mode > 0o777:
                raise ValueError

            os.umask(mode)
            print(f"Umask set to: `{format_umask_str(mode)}`")
        except ValueError:
            print(f"umask: invalid mode: '{mode_str}'")


def format_umask_str(mask):
    u = (mask >> 6) & 7
    g = (mask >> 3) & 7
    o = mask & 7

    return ",".join([
        f"u={"" if u & 4 else "r"}{"" if u & 2 else "w"}{"" if u & 1 else "x"}",
        f"g={"" if g & 4 else "r"}{"" if g & 2 else "w"}{"" if g & 1 else "x"}",
        f"o={"" if o & 4 else "r"}{"" if o & 2 else "w"}{"" if o & 1 else "x"}",
    ])