# PyShell

![](pie_shell.png)

PyShell is a simple shell built on top of the Python interpreter.
Any valid Python is also valid PyShell, and it aims to implement all the important shell features plus some extra useful ones (still in development):
- [x] custom commands
- [x] completion
- [x] file input/output redirection
- [x] command substitution
- [x] pipelines
- [ ] sharing variables between Python and shell commands
- [ ] intersperce Python and shell in a function
- [ ] background jobs / process management

## Running PyShell

```sh
git clone https://github.com/jeremymeadows/pyshell.git
cd pyshell
python -m pyshell
```

## Shell Usage

### Set environment variables
```python
> import os
> os.environ['ENV_VAR'] = 'value'
> echo $ENV_VAR
value
```

### Define aliases
```sh
> alias ls="ls --color"
> alias p="print('python in the shell')"
> p
python in the shell
```

### Use Python modules in your shell
```python
> cd ~/directory
> from math import pi
> r = 6
> 2*pi * r**2
226.1946710584651
```

### Input/Output redirection
```sh
> echo foo > out.txt
> print("bar") >> out.txt
> cat < out.txt
foo
bar
> cat < out.txt > duplicate.txt
```

### Command substitution
```sh
> ls $(os.getenv("HOME"))
Desktop Downloads Documents Music Pictures Video
> file_name = "loremipsum.txt"
> echo $(open(file_name).readlines()[0].upper())
LOREM IPSUM DOLOR SIT AMET
```

### Pipelines
```sh
> cat file.txt | cowsay | lolcat
> ls ~ | grep foo
```

## Scripting

PyShell files can interpret any valid Python code or shell commands.
They can also create custom shell commands from a Python function which can be loaded into the current enviroment using the `source` command.
By default, `~/.pyshrc` is sourced when the shell starts, and that file can be used to customize/configure PyShell.

### Create Shell Commands
Add the `command` decorator to a function to give it a name and allow it to be called as a shell command.

```python
from pyshell.commands import command

@command("myfunc")
def _myfunc(_, *args):
    print("I was passed", args)
```
```sh
> myfunc 1 2 3
I was passed ('1', '2', '3')
```

### Custom Tab Completions
A dictionary can be registered with the completer which has a prefix as the key.
If the current text matches the prefix then the value array will be presented as suggestions for the next argument.

```python
from pyshell.complete import completer

entries = {
    "docker": ["build", "run", "exec", "ps", "images", "logs", "rm", "stop", "start"],
}

try:
    # if the docker package is installed, add completions to the container's names
    import docker
    
    client = docker.from_env()
    entries["docker rm"] = []

    for c in client.containers.list():
        entries["docker rm"] += [c.name]
except ModuleNotFoundError:
    pass

completer.register(entries)
```