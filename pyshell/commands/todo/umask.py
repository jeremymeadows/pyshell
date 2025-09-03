def umask(*args):
    """
    Set or display the file mode creation mask.
    """
    import os
    import stat

    if "--help" in args or "-h" in args:
        print("Usage: umask [mode]")
        return

    if not args:
        current_umask = os.umask(0)
        os.umask(current_umask)  # Reset to original
        print(f"Current umask: {oct(current_umask)}")
        return

    mode_str = args[0]
    try:
        if mode_str.startswith("0o"):
            mode = int(mode_str, 8)
        elif mode_str.startswith("0"):
            mode = int(mode_str, 8)
        else:
            mode = int(mode_str, 8)
        
        if mode < 0 or mode > 0o777:
            raise ValueError

        os.umask(mode)
        print(f"Umask set to: {oct(mode)}")
    except ValueError:
        print(f"umask: invalid mode: '{mode_str}'")