class Foreground:
    black = '\033[30m'
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    blue = '\033[34m'
    magenta = '\033[35m'
    cyan = '\033[36m'
    white = '\033[37m'
    reset = '\033[39m'
    grey = '\033[90m'
    light_black = '\033[90m'
    light_red = '\033[91m'
    light_green = '\033[92m'
    light_yellow = '\033[93m'
    light_blue = '\033[94m'
    light_magenta = '\033[95m'
    light_cyan = '\033[96m'
    light_white = '\033[97m'

class Background:
    black = '\033[40m'
    red = '\033[41m'
    green = '\033[42m'
    yellow = '\033[43m'
    blue = '\033[44m'
    magenta = '\033[45m'
    cyan = '\033[46m'
    white = '\033[47m'
    reset = '\033[49m'
    grey = '\033[100m'
    light_black = '\033[100m'
    light_red = '\033[101m'
    light_green = '\033[102m'
    light_yellow = '\033[103m'
    light_blue = '\033[104m'
    light_magenta = '\033[105m'
    light_cyan = '\033[106m'
    light_white = '\033[107m'

class Style:
    bold = '\033[1m'
    dim = '\033[2m'
    italic = '\033[3m'
    underline = '\033[4m'
    blink = '\033[5m'
    reverse = '\033[7m'
    hidden = '\033[8m'
    strikethrough = '\033[9m'
    reset_all = '\033[0m'
    reset_bold = '\033[21m'
    reset_dim = '\033[22m'
    reset_italic = '\033[23m'
    reset_underline = '\033[24m'
    reset_blink = '\033[25m'
    reset_reverse = '\033[27m'
    reset_hidden = '\033[28m'
    reset_strikethrough = '\033[29m'

fg = Foreground()
bg = Background()
style = Style()

class TermColors:
    fg = fg
    bg = bg
    style = style

colors = TermColors()