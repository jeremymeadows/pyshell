# PyShell

![](pie_shell.png)

PyShell is a simple shell built on top of the Python interpreter.
Any valid Python is also valid PyShell, and it aims to implement all the important shell features plus some extra useful ones (features in development):
- [x] custom commands
- [x] swap between interactive and non-interactive modes
- [ ] completion
- [x] file output redirection
- [x] command substitution
- [ ] pipelines
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
> alias ll="ls -l"
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

### Output redirection
```sh
> echo foo > out.txt
> print("bar") >> out.txt
> cat out.txt
foo
bar
```

### Command substitution
```sh
> ls $(os.getenv("HOME"))
Desktop Downloads Documents Music Pictures Video
> file_name = "loremipsum.txt"
> echo $(open(file_name).readlines()[0].upper())
LOREM IPSUM DOLOR SIT AMET
```

## Scripting

PyShell files can interpret any valid Python code or shell commands.
They can also create custom shell commands from a Python function which can be loaded into the current enviromentusing the `source` command.
By default, `~/.pyshrc` is sourced when the shell starts, and that file can be used to customize/configure PyShell.

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

PyShell can also be used as an interpreter as opposed to an interactive shell via either command line arguments or by feeding in from a pipe.
Another argument can be used to swap into an interactive shell using the environment created.

```sh
> # execute a script passed in via file arguments
> pysh script.pysh
[ output of script and interpreter closes ]
```
```sh
> # run a command using a pipe then continue in the repl 
> echo "did_it_work = 'yes'" | pysh --repl
[ command executes and swaps to interactive mode ]
> print(did_it_work) # the variable can still be used
yes
```
