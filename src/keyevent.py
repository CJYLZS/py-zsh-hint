import tty
import time
import _thread


def setTimeOut(func, timeout):
    def _func():
        time.sleep(timeout)
        return func()
    _thread.start_new_thread(_func, ())


class KeyEvent:
    IGNORE = 123

    def __init__(self, callback=None) -> None:
        self.__bindkey_dict = {
            27: {
                91:
                {
                    # arrow keys
                    # 65:UP 66:DOWN 67:RIGHT 68:LEFT
                },
                79: {
                    # in zsh arrow keys is 79
                }
            }
        }
        self.__key_state_list = []
        self.__state_lock = _thread.allocate_lock()
        if callback is None or not callable(callback):
            self.callback = self.__default
        else:
            self.callback = callback

    def get_key_event(self, ordk):
        return tuple([*self.__key_state_list, ordk])

    def __default(self, ordk):
        print(self.__key_state_list, ordk, chr(ordk))

    def __timeout_clear_state(self):
        def func():
            with self.__state_lock:
                if len(self.__key_state_list) > 0:
                    tmp = self.__key_state_list.pop()
                    self.__key_state_list.clear()
                    self.callback(tmp)
        setTimeOut(func, 0.04)

    def dispatch_key_event(self, ordk):
        with self.__state_lock:
            if len(self.__key_state_list) == 0:
                # single key abcdefg
                if not ordk in self.__bindkey_dict:
                    return self.callback(ordk)
                if isinstance(self.__bindkey_dict[ordk], dict):
                    self.__key_state_list.append(ordk)
                    self.__timeout_clear_state()
                return self.IGNORE
            else:
                # multiple key alt+j alt+k
                tmp = self.__bindkey_dict[self.__key_state_list[0]]
                for tmpk in self.__key_state_list[1:]:
                    if not isinstance(tmp, dict) or tmpk not in tmp:
                        break
                    tmp = tmp[tmpk]
                if not isinstance(tmp, dict) or ordk not in tmp:
                    # callback before clear state_list
                    res = self.callback(ordk)
                    self.__key_state_list.clear()
                    return res
                if isinstance(tmp[ordk], dict):
                    self.__key_state_list.append(ordk)
                    self.__timeout_clear_state()
                return self.IGNORE

    def test(self):
        with open('/dev/tty', 'r') as fdr, open('/dev/tty', 'w') as fdw:
            tty.setcbreak(fdr)
            try:
                while True:
                    ordk = ord(fdr.read(1))
                    self.dispatch_key_event(ordk)
            except KeyboardInterrupt:
                pass


if __name__ == '__main__':
    KeyEvent().test()
