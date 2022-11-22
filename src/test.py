# s = []
# for r in range(0, 256, 10):
#     for g in range(0, 256, 10):
#         for b in range(0, 256, 10):
#             s.append(f'\033[38;2;{r};{g};{b}ma\033[0m')
#             if len(s) % 1000 == 0:
#                 s.append('\n')
# print(''.join(s))
# ESC[0J

# import time
# a = '123\n'
# print(f"\x1b[s{a*10}\x1b[u", end='')
# time.sleep(1)
# print('\x1b[0J')

import re

# b = '\x1b[0m\x1b[0m\x1b[0m\x1b[0m'
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# for i in re.finditer(ANSI_RE, b):
#     print(i.start(), i.end(), type(i))


def __ljust_str(_str):
    # [1][max_length][1]
    length = len(_str)
    max_length = 25
    if '\x1b' not in _str:
        if len(_str) <= max_length:
            return ''.join([' ', _str, ' ' * (max_length - length), '|'])
        return ''.join([' ', _str[:max_length - 3] + '...', '|'])

    _str_without_ansi_code = re.sub(ANSI_RE, '', _str)
    length = len(_str_without_ansi_code)
    if length <= max_length:
        return ''.join([' ', _str, ' ' * (max_length - length), '|'])

    max_length -= 3
    last_pos = 0
    _len = 0
    for s in re.finditer(ANSI_RE, _str):
        _len += s.start() - last_pos
        if _len > max_length:
            return ''.join([' ', _str[:last_pos + (max_length - (_len - (s.start() - last_pos)))], '\033[0m...', '|'])
        last_pos = s.end()
    return ''.join([' ', _str[:last_pos + (max_length - _len)], '\033[0m...', '|'])


print(__ljust_str('\x1b[31m' + 'a' * 1 + '\x1b[0m\x1b[0m\x1b[0m') + '1')
print(__ljust_str(
    ' ' + '../HighPerform\x1b[31man\x1b[0mceProgramming_Lab') + '1')
