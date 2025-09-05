from pyshell.complete import completer


entries = {
    "docker": ["build", "run", "exec", "ps", "images", "pull", "push", "logs", "rm"],
}

try:
    import docker
    
    client = docker.from_env()
    entries["docker rm"] = []
    entries["docker start"] = []
    entries["docker stop"] = []

    for c in client.containers.list():
        entries["docker rm"] += [c.name]
        entries["docker start"] += [c.name]
        entries["docker stop"] += [c.name]
except ModuleNotFoundError:
    pass

completer.register(entries)
