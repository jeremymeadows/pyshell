import argparse
import readline
import os


def _history(pyshenv, *args):
    parser = argparse.ArgumentParser(prog="history", description="Display the command history.")
    parser.add_argument("-c", "--clear", action="store_true", help="Clear the command history.")
    parser.add_argument("-d", "--delete", type=int, nargs="+", help="Delete a command from the history.")
    
    try:
        args = parser.parse_args(args)
    except SystemExit:
        return

    history_file = os.environ.get("HISTORY")

    if not history_file:
        print("HISTORY environment variable is not set.")
        return

    if args.clear:
        readline.clear_history()
        readline.write_history_file(history_file)
        print("history cleared")
        return
    
    if args.delete:
        for ndx in reversed(sorted(args.delete)):
            readline.remove_history_item(ndx - 1)
        readline.remove_history_item(readline.get_current_history_length() - 1)
        return

    length = readline.get_current_history_length()
    for i in range(length):
        print(f"{i + 1: >{len(str(length))}}  {readline.get_history_item(i + 1)}")