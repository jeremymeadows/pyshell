import os

def cd(path: str):
    """
    Change the current working directory.
    """
    match path:
        case None | "~":
            path = os.getenv("HOME")
        case "-":
            path = os.getenv("OLDPWD", os.getcwd())
        case _ if path.startswith("~"):
            path = os.path.join(os.getenv("HOME"), s[1:])

    os.chdir(path)
    os.environ["OLDPWD"] = os.getenv("PWD", "")
    os.environ["PWD"] = os.path.abspath(path)