import argparse

from pyshell import runner, logger

log = logger.logger(__name__)


def _source(*args):
    parser = argparse.ArgumentParser(prog="source", description="Execute commands from a file in the current shell environment.")
    parser.add_argument("files", nargs="+", help="the files to source")

    try:
        args = parser.parse_args(args)
    except SystemExit:
        return

    for file_path in args.files:
        for chunk in parse_file(file_path):
            try:
                log.debug(f"Sourcing chunk:\n{chunk}")
                if (status := runner.run(chunk)) != 0:
                    log.error(f"Command exited with status {status}")
                    return status
            except KeyboardInterrupt:
                print(f"\r{colors.fg.red}^C{colors.fg.reset}")
                continue
            except Exception as e:
                log.error(f"Error sourcing file {file_path}: {e}")
                log.exception(e)
                return 1


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