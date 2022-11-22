import re
from utils import ANSI_RE, get_terminal_size, get_cursor_pos


def get_free_terminal_size():
    x, _ = get_cursor_pos()
    lines, cols = get_terminal_size()
    return lines - x, cols


def lgreen(str):
    return f'\033[1;32m{str}\033[0m'


class TUI_Table:
    def get_table_str(self) -> str:
        if len(self.__table_list) == 0:
            return ''
        _res = []
        x = self.__selected_idx % self.__row_size
        y = self.__selected_idx // self.__row_size
        for i, row in enumerate(self.__table_matrix):
            if i == x:
                row = row.copy()
                row[y] = lgreen('>') + row[y][1:]
            _res.append(''.join(row))
        _str = '\n'.join(_res)
        return f"\033[s\n{_str}\033[u"

    def __ljust_str(self, _str):
        # [1][max_length][1]
        length = len(_str)
        max_length = self.__max_col_char - 2
        if len(_str) == 0:
            return ''
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

    def __update_table_matrix(self):
        length = len(self.__table_list)
        if length == 0:
            self.__table_matrix = [[]]
        show_list = self.__table_list.copy()
        # [1][self.__max_col_char - 2][1]
        # col_max_length = self.__max_col_char
        if length > self.__table_size:
            show_list = show_list[:self.__table_size]
        elif (tmp := length % self.__row_size) != 0:
            show_list.extend(['' for _ in range(self.__row_size - tmp)])

        cols = len(show_list) // self.__row_size
        self.__table_matrix = [list('a' * cols)
                               for _ in range(self.__row_size)]
        for i in range(cols):
            for j in range(self.__row_size):
                # idx = i * self.__row_size + j
                # if len(re.sub(ANSI_RE, '', show_list[idx])) > col_max_length:
                #     # if len(show_list[idx]) > col_max_length:
                #     # self.__table_matrix[j][i] = f"{' ' + show_list[idx][:col_max_length - 4] + '...': <{col_max_length}}|"
                #     self.__table_matrix[j][i] = self.__ljust_str()
                # else:
                #     self.__table_matrix[j][i] = f"{' ' + show_list[idx]: <{col_max_length}}|"
                self.__table_matrix[j][i] = self.__ljust_str(
                    show_list[i * self.__row_size + j])

    def set_table_size(self, col: int, row: int):
        self.__col_size = col
        self.__row_size = row
        self.__table_size = self.__col_size * self.__row_size
        self.__update_table_matrix()

    def set_table_list(self, data: list):
        self.__table_list = data
        self.__selected_idx = 0
        self.__update_table_matrix()

    def set_select_idx(self, idx: int):
        if idx >= len(self.__table_list):
            idx = len(self.__table_list) - 1
        elif idx < 0:
            idx = 0
        self.__selected_idx = idx

    def move_right(self):
        tmp = self.__selected_idx
        tmp += self.__row_size
        if tmp >= len(self.__table_list):
            tmp %= self.__row_size
        self.__selected_idx = tmp

    def move_left(self):
        tmp = self.__selected_idx
        tmp -= self.__row_size
        if tmp < 0:
            tmp = (len(self.__table_list) - 1) // self.__row_size * \
                self.__row_size + (self.__selected_idx % self.__row_size)
        self.__selected_idx = tmp

    def move_up(self):
        tmp = self.__selected_idx
        tmp -= 1
        if tmp < 0:
            tmp = len(self.__table_list) - 1
        self.__selected_idx = tmp

    def move_down(self):
        tmp = self.__selected_idx
        tmp += 1
        if tmp >= len(self.__table_list):
            tmp = 0
        self.__selected_idx = tmp

    def get_table_list(self) -> list:
        return self.__table_list

    def get_table_size(self) -> int:
        return self.__table_size

    def get_selected_idx(self) -> int:
        return self.__selected_idx

    def get_selected_item(self) -> str:
        return self.__table_list[self.__selected_idx]

    def __init__(self, max_col_char=25) -> None:
        if max_col_char < 10:
            max_col_char = 10
        self.__table_list = []
        self.__table_matrix = [[]]
        self.__selected_idx = 0
        self.__row_char_size, self.__col_char_size = get_free_terminal_size()
        self.__max_col_char = max_col_char
        self.__col_size = self.__col_char_size // max_col_char
        self.__row_size = self.__row_char_size
        if self.__row_size <= 0:
            self.__row_size = 1
        self.__table_size = self.__col_size * self.__row_size


if __name__ == '__main__':
    import time
    table = TUI_Table()
    tlist = ['a' * 26, 'bbb', 'ccc', 'd' * 26, 'eee', 'fff', 'ggg']
    tlist = ['a', 'b', 'c']
    # tlist = []
    table.set_table_list(tlist)
    for i in range(len(tlist) + 5):
        # table.set_select_idx(i)
        table.move_left()
        print(table.get_table_str(), end='')
        time.sleep(500)
