def fg(*args):
    """
    Resume a job in the foreground.
    """
    import os
    import signal
    import subprocess
    import time

    if not args or args[0] in ("--help", "-h"):
        print("Usage: fg <job_id>")
        return

    try:
        job_id = int(args[0])
    except ValueError:
        print(f"fg: {args[0]}: invalid job ID")
        return

    if job_id not in jobs:
        print(f"fg: {job_id}: no such job")
        return

    job = jobs[job_id]
    pid = job['pid']
    command = job['command']

    try:
        os.kill(pid, signal.SIGCONT)
        print(f"Resuming job [{job_id}] {command} (PID {pid})")
        
        # Wait for the process to complete
        while True:
            try:
                _, status = os.waitpid(pid, 0)
                if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                    break
            except ChildProcessError:
                break
            except KeyboardInterrupt:
                os.kill(pid, signal.SIGINT)
                print(f"\r{colors.fg.red}^C{colors.fg.reset}")
                break
            time.sleep(0.1)

        del jobs[job_id]
        print(f"Job [{job_id}] {command} completed")
    except ProcessLookupError:
        print(f"fg: {job_id}: no such process")
    except Exception as e:
        print(f"fg: error resuming job {job_id}: {e}")