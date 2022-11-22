import re
import os
import tty
import time
import _thread

# Regex for ANSI colour codes
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
DO_NOTHING = 0
RUN_CMD = 1
CANCEL = 130


def red(str):
    return f'\033[31m{str}\033[0m'


def green(str):
    return f'\033[32m{str}\033[0m'
    # return f'$[green]{str}$reset_color'


def yellow(str):
    return f'\033[33m{str}\033[0m'


def blue(str):
    return f'\033[34m{str}\033[0m'


def purple(str):
    return f'\033[35m{str}\033[0m'


def cyan(str):
    return f'\033[36m{str}\033[0m'


def lred(str):
    return f'\033[1;31m{str}\033[0m'


def get_terminal_size():
    try:
        return int(os.environ["LINES"]), int(os.environ["COLUMNS"])
    except:
        tmp = os.get_terminal_size()
        return tmp.lines, tmp.columns


def get_cursor_pos():
    # x: line_index
    # y: column_index
    '''
        echo -ne '\u001b[6n' > /dev/tty
        read -t 1 -s -d 'R' pos < /dev/tty
        pos="${pos##*\[}"
        row="$(( ${pos%;*} -1 ))"
        col="$(( ${pos#*;} -1 ))"
        echo $row $col
    '''
    with open('/dev/tty', 'w') as f:
        f.write('\u001b[6n')
    with open('/dev/tty', 'r') as f:
        tty.setcbreak(f)
        tmp = ''
        while True:
            x = f.read(1)
            if x == 'R':
                break
            tmp += x
    x, y = tmp[2:].split(';')
    return int(x), int(y)


def setTimeOut(func, timeout):
    def _func():
        time.sleep(timeout)
        return func()
    _thread.start_new_thread(_func, ())
