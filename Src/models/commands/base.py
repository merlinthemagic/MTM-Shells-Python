"""
Mirrors Src/Models/Commands/Base.php
"""
import time
import uuid


class Base:

    def __init__(self):
        if type(self) is Base:
            raise TypeError("Base is abstract and cannot be instantiated directly")

        self._guid = None
        self._is_exec = False
        self._is_running = False
        self._is_done = False
        self._parent_obj = None
        self._str_cmd = None
        self._find_cmd = True  # set False when the return won't include the command, e.g. password logins
        self._reg_exp = None
        self._commit = None
        self._exec_time = None
        self._init_time = None
        self._done_time = None
        self._timeout = 25000
        self._data = ""
        self._error = None

    def get_guid(self):
        if self._guid is None:
            self._guid = str(uuid.uuid4())
        return self._guid

    def set_parent(self, obj):
        self._parent_obj = obj
        return self

    def get_parent(self):
        return self._parent_obj

    def set_cmd(self, str_cmd):
        self._str_cmd = str_cmd
        return self

    def get_cmd(self):
        return self._str_cmd

    def set_delimitor(self, reg_exp):
        self._reg_exp = reg_exp
        return self

    def get_delimitor(self):
        return self._reg_exp

    def set_commit(self, chars):
        self._commit = chars
        return self

    def get_commit(self):
        return self._commit

    def set_timeout(self, ms):
        self._timeout = ms
        return self

    def get_timeout(self):
        return self._timeout

    def set_find_command(self, val):
        self._find_cmd = val
        return self

    def get_find_command(self):
        return self._find_cmd

    def get_is_exec(self):
        return self._is_exec

    def get_is_running(self):
        return self._is_running

    def get_run_time(self):
        """Returns elapsed run time in milliseconds."""
        if self._init_time is not None:
            if self.get_is_done() is False:
                return (time.time() - self._init_time) * 1000
            else:
                return (self._done_time - self._init_time) * 1000
        return 0

    def get_is_done(self, refresh=False):
        if refresh is True:
            self._check_data()
        return self._is_done

    def set_running(self):
        # triggered by parent
        if self._is_running is False:
            self._is_running = True
            self._init_time = time.time()
        return self

    def set_done(self):
        if self._is_done is False:
            self._is_done = True
            self._done_time = time.time()
        return self

    def read_once(self):
        """Helpful when running many shells and checking if a command is finished."""
        if self._is_done is False:
            if self._is_exec is False:
                self.exec()
            self.get_parent().read(self)
        return self

    def exec(self):
        if self._is_exec is False:
            self.get_parent().execute(self)
            self._is_exec = True
            self._exec_time = time.time()
        return self

    def add_data(self, data):
        self._data += data
        return self

    def get_data(self):
        return self._data

    def get_parsed_data(self):
        return self._parse()

    def get_return_data(self):
        return self._remove_command()

    def set_error(self, e):
        self._error = e
        self.set_done()
        return self

    def get_error(self):
        return self._error

    def get(self, throw=True):
        self.exec()
        while True:
            self.get_parent().read(self)
            if self.get_is_done(True) is False:
                time.sleep(0.01)  # this structure has to go (kept for parity with the original)
            elif self._error is None:
                return self.get_parsed_data()
            elif throw is True:
                raise self._error
            else:
                return self._data

    # --- to be implemented by subclasses (e.g. Bash) ---

    def _check_data(self):
        raise NotImplementedError

    def _parse(self):
        raise NotImplementedError

    def _remove_command(self):
        raise NotImplementedError
