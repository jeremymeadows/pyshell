def disown(*args):
    """
    Disown a job.
    """
    if "--help" in args or "-h" in args:
        print("Usage: disown [job_id]")
        return

    print("Disowning jobs is not implemented yet.")