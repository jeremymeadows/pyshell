import argparse
import os
import signal
import sys
import termios

from pyshell import pyshenv, logger

log = logger.logger(__name__)


def _fg(*args):
    parser = argparse.ArgumentParser(prog="fg", description="Move a job to the foreground.")
    parser.add_argument("id", type=int, nargs="?", help="specifies the job IDs to move (default: highest id)")

    try:
        args = parser.parse_args(args)
    except SystemExit:
        return

    job_id = args.id or (max(pyshenv.jobs) if pyshenv.jobs else None)
    if not job_id or job_id not in pyshenv.jobs:
        print("fg: no current job")
        return

    log.debug(f"Bringing job {job_id} to foreground")
    job = pyshenv.jobs[job_id]

    try:
        old_pgrp = os.tcgetpgrp(sys.stdin.fileno())
        old_attr = termios.tcgetattr(sys.stdin.fileno())

        # set the child's process group as new foreground
        os.tcsetpgrp(sys.stdin.fileno(), job.proc.pid)
        # revive the child in case it was stopped before it was made foreground
        job.proc.send_signal(signal.SIGCONT)
        job.status = 'running'
        job.notified = False

        status = os.waitpid(job.proc.pid, os.WUNTRACED)[1]

        # if stopped from a signal
        if os.WIFSTOPPED(status):
            log.debug(f"process {job.proc.pid} stopped")
            job.status = 'stopped'
            job.notified = False

            status = 0
            print()
        else:
            del pyshenv.jobs[job_id]
    finally:
        # Restore the default SIGTSTP behavior
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)

        # ignore signals from changing tty
        old_hdlr = signal.signal(signal.SIGTTOU, signal.SIG_IGN)
        # make parent group foreground again
        os.tcsetpgrp(sys.stdin.fileno(), old_pgrp)
        # restore the handler
        signal.signal(signal.SIGTTOU, old_hdlr)
        # restore terminal attributes
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_attr)
    return status