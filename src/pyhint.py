import os
import sys
import tty

sys.path.insert(0, os.path.join(os.path.realpath(__file__)))
from table import TUI_Table
from keyevent import KeyEvent
from utils import *


class PyHint(KeyEvent):
    BACKSPACE = 127
    ENTER = 10
    ESCAPE = 27
    TAB = 9
    LEFT = 104      # h
    DOWN = 106      # j
    UP = 107        # k
    RIGHT = 108     # l
    HISTORY_BACK = 98       # b
    HISTORY_FORWARD = 111   # o
    DIR_UP = 112            # p
    # Regex for ANSI colour codes
    ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
    HINT_START = cyan(' >> ')

    def get_alias(self):
        _str = os.environ.get("ALIAS", "")
        res = []
        for line in _str.split('\n'):
            if len(line) == 0:
                continue
            name, *value = line.split('=')
            value = '='.join(value).strip("'")
            res.append((name, value))
        return res

    def get_executable(self):
        for path in os.environ["PATH"].split(":"):
            for f in os.scandir(path):
                if os.access(f.path, os.X_OK):
                    self.execuable_list.append(f.name)

        self.alias_dict = {}
        for alias, cmd in self.get_alias():
            self.execuable_list.append(alias)
            self.alias_dict[alias] = cmd

    def __init__(self) -> None:
        super().__init__(callback=self.handle_keyevent)
        self.__table = TUI_Table()
        self.key_map = {
            self.BACKSPACE: '\b \b'
        }
        self.buffer = []
        self.buffer_str = ''
        self.command_map = {
            'cd': self.handle_cd
        }
        self.execuable_list = []
        self.get_executable()
        self.event_handle_map = {
            (self.ESCAPE, self.LEFT): self.move_left,
            (self.ESCAPE, self.DOWN): self.move_down,
            (self.ESCAPE, self.UP): self.move_up,
            (self.ESCAPE, self.RIGHT): self.move_right,
            (self.ESCAPE, self.HISTORY_BACK): self.move_history_back,
            (self.ESCAPE, self.HISTORY_FORWARD): self.move_history_forward,
            (self.ESCAPE, self.DIR_UP): self.try_dir_up
        }
        self.suggestion_list = []
        self.suggestion_history_back_list = []
        self.suggestion_history_forward_list = []

        self.CAN_SOURCE_LIST = ['cd']

        self.completion_type = None  # 'cmd' or 'filename'
        self.completion_word = ''
        self.completion_cmd = ''

    def move_up(self):
        self.__table.move_up()
        self._flush_table()
        return self.IGNORE

    def move_down(self):
        self.__table.move_down()
        self._flush_table()
        return self.IGNORE

    def move_left(self):
        self.__table.move_left()
        self._flush_table()
        return self.IGNORE

    def move_right(self):
        self.__table.move_right()
        self._flush_table()
        return self.IGNORE

    def clear_suggestion_area(self, flush=False):
        sys.stderr.write('\x1b[0J')
        if flush:
            sys.stderr.flush()

    def _flush_table(self, flush=False):
        self.clear_suggestion_area(flush=flush)
        sys.stderr.write(self.__table.get_table_str())

    def flush_table(self, new_table_list: list):
        self.__table.set_table_list(new_table_list)
        self._flush_table(flush=True)

    def handle_cmd(self) -> list:
        suggestion_tmp_list = set()
        for cmd in self.execuable_list:
            if cmd.startswith(self.completion_word):
                if cmd in self.alias_dict:
                    tmp = ''.join((cmd, self.HINT_START, self.alias_dict[cmd]))
                    colored_tmp = tmp.replace(
                        self.completion_word, red(self.completion_word))
                    suggestion_tmp_list.add((len(tmp), tmp, colored_tmp))
                else:
                    suggestion_tmp_list.add((len(cmd), cmd, (cmd).replace(
                        self.completion_word, red(self.completion_word))))
        suggestion_tmp_list = sorted(suggestion_tmp_list, key=lambda s: s[0])
        self.suggestion_list = [s[1] for s in suggestion_tmp_list]
        return [s[2] for s in suggestion_tmp_list]

    def handle_cd(self) -> list:
        sep = os.path.sep
        path = self.completion_word
        if path.startswith('~'):
            path = os.path.expanduser(path)

        pos = path.rfind(sep)
        base_dir = path[:pos + 1] if pos != -1 else '.'
        dest_dir = path[pos + 1:]
        self.suggestion_list = []
        max_size = self.__table.get_table_size()
        try:
            if len(dest_dir) == 0:
                # list all dir
                for f in os.scandir(base_dir):
                    if f.is_dir():
                        self.suggestion_list.append(f.name + sep)
                        if len(self.suggestion_list) == max_size:
                            break
                return self.suggestion_list
            else:
                # list and highlight specified dir
                suggestion_tmp_list = []
                # [[pos, ]]
                for f in os.scandir(base_dir):
                    pos = f.name.find(dest_dir)
                    if pos != -1 and f.is_dir():
                        tmp = f.name + sep
                        colored_tmp = tmp.replace(dest_dir, red(dest_dir))
                        suggestion_tmp_list.append((pos, tmp, colored_tmp))
                        if len(suggestion_tmp_list) == max_size:
                            break
                suggestion_tmp_list = sorted(
                    suggestion_tmp_list, key=lambda k: k[0])
                self.suggestion_list = [s[1] for s in suggestion_tmp_list]
                return [s[2] for s in suggestion_tmp_list]
        except Exception as e:
            # return '\n ' + red(f"{e}")
            return [red(f"{e}")]

    def handle_default(self) -> list:
        # complete any file
        sep = os.path.sep
        path = self.completion_word
        if path.startswith('~'):
            path = os.path.expanduser(path)

        pos = path.rfind(sep)
        base_dir = path[:pos + 1] if pos != -1 else '.'
        dest_dir = path[pos + 1:]
        self.suggestion_list = []
        suggestion_tmp_list = []
        max_size = self.__table.get_table_size()
        try:
            for f in os.scandir(base_dir):
                pos = f.name.find(dest_dir)
                if pos != -1:
                    colored_tmp = f.name.replace(dest_dir, red(dest_dir))
                    suggestion_tmp_list.append(
                        (pos, f.name, colored_tmp, f.is_dir()))
                    if len(suggestion_tmp_list) == max_size:
                        break
            suggestion_tmp_list = sorted(
                suggestion_tmp_list, key=lambda k: (k[3], k[0]))
            self.suggestion_list = [s[1] for s in suggestion_tmp_list]
            return [s[2] for s in suggestion_tmp_list]
        except Exception as e:
            # return '\n ' + red(f"{e}")
            return [red(f"{e}")]

    def update_buffer(self, ordk=None, new_buffer_str=None):
        if ordk is not None:
            if ordk == self.BACKSPACE:
                if len(self.buffer) == 0:
                    return self.IGNORE
                self.buffer.pop()
            elif chr(ordk).isprintable():
                self.buffer.append(chr(ordk))
            self.buffer_str = ''.join(self.buffer)

        if isinstance(new_buffer_str, str):
            self.buffer = [ch for ch in new_buffer_str]
            self.buffer_str = new_buffer_str

        if ' ' not in self.buffer_str:
            self.completion_type = 'cmd'
            self.completion_word = self.buffer_str
        else:
            self.completion_type = 'filename'
            tmp = self.buffer_str.split(' ')
            self.completion_cmd = tmp[0]
            self.completion_word = tmp[-1]

        return True

    def update_suggestion(self):
        if self.completion_type == 'cmd':
            # command completion
            suggestion_list = self.handle_cmd()
        elif self.completion_cmd in self.command_map:
            # special completion
            suggestion_list = self.command_map[self.completion_cmd]()
        else:
            # normal completion
            suggestion_list = self.handle_default()
        self.flush_table(suggestion_list)

    def expand_suggest(self, suggest):
        sep = os.path.sep
        if self.buffer_str.endswith(sep):
            return self.buffer_str + suggest
        cmd, *args = self.buffer_str.split(' ')
        word = args[-1]
        pos = word.rfind(sep)
        if pos == -1:
            return ' '.join([cmd] + args[:-1] + [suggest])
        word = word[:pos + 1]
        return ' '.join([cmd] + args[:-1] + [word + suggest])

    def set_selected_suggest(self, suggest: str = None):
        old_length = len(self.buffer_str)
        if isinstance(suggest, str):
            res = suggest
        else:
            res = ''
            if len(self.suggestion_list) == 0:
                return res
            self.suggestion_history_forward_list.clear()
            self.suggestion_history_back_list.append(self.buffer_str)
            idx = self.__table.get_selected_idx()
            if self.completion_type == 'cmd':
                res = self.suggestion_list[idx]
            else:
                res = self.expand_suggest(self.suggestion_list[idx])
            if (pos := res.find(self.HINT_START)) != -1:
                res = res[:pos].strip()
        res = re.sub(self.ANSI_RE, '', res)  # remove color
        self.update_buffer(new_buffer_str=res)
        self.update_suggestion()
        return '\b \b' * old_length + self.buffer_str

    def move_history_back(self) -> str:
        if len(self.suggestion_history_back_list) == 0:
            return ''

        self.suggestion_history_forward_list.append(self.buffer_str)
        return self.set_selected_suggest(suggest=self.suggestion_history_back_list.pop())

    def move_history_forward(self) -> str:
        if len(self.suggestion_history_forward_list) == 0:
            return ''
        self.suggestion_history_back_list.append(self.buffer_str)
        return self.set_selected_suggest(suggest=self.suggestion_history_forward_list.pop())

    def try_dir_up(self) -> str:
        if os.path.sep not in self.completion_word:
            return self.IGNORE
        if self.buffer_str.endswith(os.path.sep):
            _str = self.buffer_str[:self.buffer_str[:-
                                                    1].rfind(os.path.sep) + 1]
        else:
            _str = self.buffer_str[:self.buffer_str.rfind(os.path.sep) + 1]
        return self.set_selected_suggest(suggest=_str)

    def get_ret_code(self):
        if self.completion_type == 'cmd':
            return DO_NOTHING
        return RUN_CMD

    def handle_keyevent(self, ordk):
        keys_tuple = self.get_key_event(ordk)
        if len(keys_tuple) == 1:
            if ordk == self.ENTER:
                return self.get_ret_code()  # normal finish
            elif ordk == self.TAB:
                return self.set_selected_suggest()
            ret = self.update_buffer(ordk=ordk)
            self.update_suggestion()
            return ret

        if keys_tuple in self.event_handle_map:
            return self.event_handle_map[keys_tuple]()

        return self.IGNORE

    def finish(self):
        self.clear_suggestion_area(flush=True)
        sys.stdout.write(self.buffer_str)

    def try_complete_part(self):
        # find longest prefix
        if len(self.suggestion_list) == 0:
            return
        s = len(self.completion_word) + 1
        part = self.completion_word
        tmp_list = sorted(
            [s for s in self.suggestion_list if s.startswith(part)], key=lambda s: len(s), reverse=True)
        if len(tmp_list) == 0:
            return
        elif len(tmp_list) == 1:
            part = tmp_list[0] + ' '
        else:
            longest_str = tmp_list[0]
            shortest_str = tmp_list[-1]
            while True:
                b = False
                tmp = longest_str[:s]
                for suggestion in tmp_list:
                    if not suggestion.startswith(tmp):
                        b = True
                        break
                if b:
                    break
                part = tmp
                s += 1
                if s > len(shortest_str):
                    break
        self.fdw.write('\b' * len(self.buffer_str))
        if self.completion_type == 'cmd':
            self.update_buffer(new_buffer_str=part)
        else:
            self.update_buffer(new_buffer_str=self.expand_suggest(part))
        self.fdw.write(self.buffer_str)
        self.fdw.flush()

    def main(self):
        ret = DO_NOTHING
        with open('/dev/tty', 'r') as self.fdr, open('/dev/tty', 'w') as self.fdw:
            tty.setcbreak(self.fdr)
            self.update_buffer(new_buffer_str=os.environ.get("BUFFER", ""))
            self.update_suggestion()
            self.try_complete_part()
            self.update_suggestion()
            try:
                while True:
                    key = self.fdr.read(1)
                    ordk = ord(key)
                    if (res := self.dispatch_key_event(ordk)) != self.IGNORE:
                        if res is not True and isinstance(res, int):
                            ret = res
                            self.finish()
                            break
                        if isinstance(res, str):
                            self.fdw.write(res)
                        else:
                            self.fdw.write(self.key_map.get(ordk, key))
                        self.fdw.flush()
            except KeyboardInterrupt:
                self.finish()
                return CANCEL
        return ret


if __name__ == '__main__':
    ret = PyHint().main()
    sys.exit(ret)
