import subprocess

def exec(args):
    """Execute a command."""

    try:
        result = subprocess.run(args, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e.stderr}")