import argparse
import os
import signal

from pyshell import logger

log = logger.logger(__name__)


def _disown(pyshenv, *args):
    parser = argparse.ArgumentParser(prog="disown", description="Remove jobs from the current shell.")
    parser.add_argument("id", nargs="*", help="specifies the job IDs to disown (default: highest id)")
    parser.add_argument("-a", "--all", action="store_true", help="disown all jobs")
    parser.add_argument("-r", "--running", action="store_true", help="disown only running jobs")
    parser.add_argument("-s", "--start", action="store_true", help="restart stopped jobs before disowning them")
    parser.add_argument("-f", "--force", action="store_true", help="force disowning jobs even if they are stopped")
    parser.add_argument("-n", "--nohup", action="store_true", help="mark jobs so they will be disowned when the shell receives SIGHUP")

    try:
        args = parser.parse_args(args)
    except SystemExit:
        return

    for job_id in (pyshenv.jobs if args.all else args.id or [max(pyshenv.jobs or [None])]):
        if not (job := pyshenv.jobs.get(job_id)):
            print(f"disown: no such job {job_id}")
            continue

        if args.running and job.status != "running":
            continue
        if not args.force and job.status == "stopped":
            print(f"disown: ignoring stopped job {job_id}")
            continue

        if args.nohup:
            job.nohup = True
        else:
            del pyshenv.jobs[job_id]
            log.debug(f"[{job_id}] disowned")

