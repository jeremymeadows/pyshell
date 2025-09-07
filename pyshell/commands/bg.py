import argparse
import signal

from pyshell import pyshenv, logger

log = logger.logger(__name__)


def _bg(*args):
    parser = argparse.ArgumentParser(prog="bg", description="Move jobs to the background.")
    parser.add_argument("id", type=int, nargs="*", help="specifies the job IDs to move (default: highest id)")
    parser.add_argument("-a", "--all", action="store_true", help="move all jobs to background")

    try:
        args = parser.parse_args(args)
    except SystemExit:
        return

    if not pyshenv.jobs:
        print("bg: no current jobs")
        return

    for job_id in (pyshenv.jobs if args.all else args.id or [max(pyshenv.jobs or [None])]):
        if not (job := pyshenv.jobs.get(job_id)):
            print(f"bg: {job_id}: no such job")
            continue

        log.debug(f"Resuming job {job_id} in background")
        job.proc.send_signal(signal.SIGCONT)
        job.status = 'running'
        job.notified = False