import argparse

from pyshell import runner

def _eval(pyshenv, *args):
    parser = argparse.ArgumentParser(prog="eval", description="Evaluate a PyShell expression.")
    parser.add_argument("expression", nargs="*", help="the expression to evaluate")
    
    try:
        parser.parse_args(args)
    except SystemExit:
        return

    input_str = " ".join(args).strip()
    runner.run_pipeline(runner.parse(input_str))