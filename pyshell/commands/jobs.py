import argparse

from pyshell import pyshenv, logger

log = logger.logger(__name__)


def _jobs(*args):
    parser = argparse.ArgumentParser(prog="jobs", description="Display status of background jobs.")
    parser.add_argument("id", nargs="*", help="specifies the job IDs to list (default: all jobs)")
    parser.add_argument("-l", "--long", action="store_true", help="lists process IDs in addition to the normal information")
    parser.add_argument("-n", "--notify", action="store_true", help="lists only jobs that have changed status since the last notification")
    parser.add_argument("-p", "--pid", action="store_true", help="lists only the process IDs of the jobs")
    parser.add_argument("-r", "--running", action="store_true", help="lists only running jobs")
    parser.add_argument("-s", "--stopped", action="store_true", help="lists only stopped jobs")

    try:
        args = parser.parse_args(args)
    except SystemExit:
        return

    done = []
    for job_id, job in pyshenv.jobs.items():
        if job.status == 'running' and job.proc.poll() is not None:
            job.status = 'done'
            job.notified = False

        if args.id and job_id not in args.id:
            continue
        if args.running and job.status != 'running':
            continue
        if args.stopped and job.status != 'stopped':
            continue
        if args.notify and job.notified:
            continue

        if args.pid:
            print(job.proc.pid)
            continue

        line = f"[{job_id}]"
        if args.long:
            line += f"({job.proc.pid})"
        print(line + ("!" if job.nohup else " "), job)

        job.notified = True
        if job.status == "done":
            done += [job_id]
    
    for job_id in done:
        del pyshenv.jobs[job_id]