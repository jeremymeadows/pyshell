# PyShell
![](pie_shell.png)

PyShell is a simple shell built on top of the Python interpreter.
Any valid Python is also valid PyShell, and it aims to implement all the important shell features plus some extra useful ones:
- [x] custom commands
- [x] swap between interactive and non-interactive modes
- [ ] completion
- [ ] pipelines
- [ ] file output redirection
- [ ] sharing variables between python and shell commands
- [ ] intersperce Python and shell in a single function
- [ ] background jobs / process management

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

### Use python modules in your shell
```python
> cd ~/directory
> from math import pi
> r = 6
> 2*pi * r**2
226.1946710584651
```

## Scripting

PyShell files can interpret any valid Python code or shell commands.
They can also create custom shell commands from a Python function which can be loaded into the current enviromentusing the `source` command.
A `.pyshrc` is sourced when the shell starts, and that file can be used to customize/configure PyShell.

```python
from commands import command

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
$ python shell.py script.pysh # using file arguments
[ output of script and interpreter closes ]
$ echo "did_it_work = 'yes'" | python shell.py --noexit # using pipe
[ output of script and swap to interactive mode ]
> print(did_it_work) # now in the repl
yes
```
