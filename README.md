# PyShell

![](pie_shell.png)

PyShell is a simple shell built on top of the Python interpreter.
Any valid Python is also valid PyShell, and it aims to implement all the important shell features plus some extra useful ones:
- [x] custom commands
- [x] completion
- [x] file input/output redirection
- [x] command substitution
- [x] pipelines
- [x] read shell variables from Python
- [x] run shell commands from a Python function
- [x] background jobs / process management

## Running PyShell

```sh
git clone https://github.com/jeremymeadows/pyshell.git
cd pyshell
python -m pyshell
```

## Shell Usage

### Set environment variables
```python
> # using Python `environ` dict
> import os
> os.environ["ENV_VAR1"] = "value"
> # exporting new variable (creates Python variable ENV_VAR2 and adds to `environ`)
> export ENV_VAR2 = "second variable"
> # exporting existing variable
> ENV_VAR3 = 7
> export ENV_VAR3
>
> echo $ENV_VAR1 $ENV_VAR2 $ENV_VAR3
value second variable 7
```

### Define aliases
```sh
> # quotes are optional unless they are used to preserve spaces, like in filenames, for example
> alias ls = ls --color
> alias proj = cd "~/Projects/project with space/"
> alias p = print("python in the shell")
> p
python in the shell
```

### Use double/single quotes to control expansion
```sh
> export DIR = "foo bar"
> ls
> bar/   foo/  'foo bar'/
> ls $DIR
bar:
foo:
> ls "$DIR"
'foo bar':
> ls '$DIR'
ls: cannot access '$DIR': No such file or directory
```

### File input/output redirection
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

### Variable expansion
```sh
> import os
>
> os.environ["NUMBER"] = "2"
> pow($NUMBER, 7) - 1
127
>
> os.environ["NAME"] = "jeremy"
> print("hello $NAME")
hello jeremy
```

### Pipelines
```sh
> cat file.txt | cowsay | lolcat
> ls ~ | grep filename
```

### Job control
```sh
> vlc video.mp4
^Z
> jobs
[1]  stopped  vlc video.mp4
> bg
> jobs
[1]  running  vlc video.mp4
> disown
> jobs
> exit
```

## Scripting

PyShell can interpret any valid Python code or shell commands.
It also supports creating custom shell commands from a Python function which can be loaded into the current enviroment using the `source` command.
By default, `~/.pyshrc` is sourced when the shell starts, and that file can be used to customize/configure PyShell.

### Create shell commands
Add the `command` decorator to a function to give it a name and allow it to be called as a shell command.

```python
from pyshell.commands import command

@command("myfunc")
def _myfunc(*args):
    print("I was passed", args)
```
```sh
> myfunc 1 2 3
I was passed ('1', '2', '3')
```

### Command substitution
Command substitution can also be used in scripts to run shell commands.
Strings and string lists are both valid.

```python
from pyshell.commands import command

@command("rcow")
def _rainbowcow_command(*args):
    """A command that prints a rainbow cow talking"""
    if not args:
        $("cowsay Moo | lolcat")
    else:
        $(["cowsay", *args, "| lolcat"])
```

### Custom tab completions
A dictionary can be registered with the completer which has a prefix as the key.
If the current text matches the prefix then the value array will be presented as suggestions for the next argument.

```python
from pyshell.complete import completer

entries = {
    "docker": ["build", "run", "exec", "ps", "images", "logs", "rm", "stop", "start"],
}

try:
    # if the docker package is installed, add completions to the container names
    import docker
    
    client = docker.from_env()
    entries["docker rm"] = []

    for c in client.containers.list():
        entries["docker rm"] += [c.name]
except ModuleNotFoundError:
    pass

completer.register(entries)
```