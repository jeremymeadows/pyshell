import os, signal, socket, sys

from pyshell import logger

__version__ = "0.3.0"
log = logger.logger(__name__)


def prompt():
    return f"{{user}} {{cwd}} > "


class Job:
    def __init__(self, process):
        self.proc = process
        self.status = "stopped"
        self.notified = False
        self.nohup = False
    
    def __repr__(self):
        return f"{self.status:8} {" ".join(self.proc.args)}"


class PyShellEnv:
    def __init__(self):
        self.namespace = { "prompt": prompt }
        self.interactive = sys.stdin.isatty()
        self.repl = True
        self.help = ""
        self.aliases = dict()
        self.prompt_subs = {
            "user": os.getlogin(),
            "host": socket.gethostname(),
            "cwd": lambda: os.path.join(os.getcwd().replace(os.getenv("HOME", "~"), "~"), ""),
        }
        self.jobs = dict()
    
    def add_job(self, process):
        self.jobs[max(self.jobs or [0]) + 1] = Job(process)

pyshenv = PyShellEnv()


def handle_sighup(*_):
    log.debug("Sending SIGHUP to all jobs")
    for job_id, job in pyshenv.jobs.items():
        if not job.nohup:
            try:
                job.proc.send_signal(signal.SIGHUP)
                log.debug(f"[{job_id}] sent SIGHUP")
            except ProcessLookupError:
                pass

signal.signal(signal.SIGHUP, handle_sighup)


import importlib, pkgutil
__all__ = [module.name for module in pkgutil.iter_modules(__path__) if module.name != '__main__']
for module in __all__:
    importlib.import_module(f"{__name__}.{module}")
__all__ += ["pyshenv"]