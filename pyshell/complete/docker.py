from pyshell.complete import completer


entries = {
    "docker": ["build", "run", "exec", "ps", "image", "pull", "push", "logs", "rm"],
    "docker image": ["build", "history", "import", "inspect", "load", "ls", "prune", "pull", "push", "rm", "save", "tag"],
}


try:
    import docker
    
    def container_names():
        client = docker.from_env()
        return [c.name for c in client.containers.list(all=True)]

    completer.register_dynamic("docker rm", container_names)
except ModuleNotFoundError:
    pass

completer.register(entries)