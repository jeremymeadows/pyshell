import argparse
# import traceback

def _source(pyshenv, *args):
    parser = argparse.ArgumentParser(prog="source", description="Execute commands from a file in the current shell environment.")
    parser.add_argument("files", nargs="+", help="the files to source")

    try:
        args = parser.parse_args(args)
    except SystemExit:
        return

    for file_path in args.files:
        for chunk in parse_file(file_path):
            try:
                pyshenv.run(chunk)
            except KeyboardInterrupt:
                print(f"\r{colors.fg.red}^C{colors.fg.reset}")
                continue
            # except Exception as e:
            #     suggestion = traceback.format_exception(e)[-1].strip()
            #     print(f"{colors.fg.red}{suggestion}{colors.fg.reset}")
            #     return 1

def parse_file(file_path):
    with open(file_path, "r") as file:
        chunks = []
        prev = ""

        for line in file:
            if line and not line.isspace() and not line.lstrip().startswith("#"):
                if len(line) - len(line.lstrip()) == 0 and not prev.startswith("@"):
                    chunks += [line]
                else:
                    chunks[-1] += line
            prev = line
    return [c.rstrip("\n") for c in chunks]