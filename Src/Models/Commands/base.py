
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

    def getGuid(self):
        if self._guid is None:
            self._guid = str(uuid.uuid4())
        return self._guid

    def setParent(self, obj):
        self._parent_obj = obj
        return self

    def getParent(self):
        return self._parent_obj

    def setCmd(self, str_cmd):
        self._str_cmd = str_cmd
        return self

    def getCmd(self):
        return self._str_cmd

    def setDelimitor(self, reg_exp):
        self._reg_exp = reg_exp
        return self

    def getDelimitor(self):
        return self._reg_exp

    def setCommit(self, chars):
        self._commit = chars
        return self

    def getCommit(self):
        return self._commit

    def setTimeout(self, ms):
        self._timeout = ms
        return self

    def getTimeout(self):
        return self._timeout

    def setFindCommand(self, val):
        self._find_cmd = val
        return self

    def getFindCommand(self):
        return self._find_cmd

    def getIsExec(self):
        return self._is_exec

    def getIsRunning(self):
        return self._is_running

    def getRunTime(self):
        """Returns elapsed run time in milliseconds."""
        if self._init_time is not None:
            if self.getIsDone() is False:
                return (time.time() - self._init_time) * 1000
            else:
                return (self._done_time - self._init_time) * 1000
        return 0

    def getIsDone(self, refresh=False):
        if refresh is True:
            self._check_data()
        return self._is_done

    def setRunning(self):
        # triggered by parent
        if self._is_running is False:
            self._is_running = True
            self._init_time = time.time()
        return self

    def setDone(self):
        if self._is_done is False:
            self._is_done = True
            self._done_time = time.time()
        return self

    def readOnce(self):
        """Helpful when running many Shells and checking if a command is finished."""
        if self._is_done is False:
            if self._is_exec is False:
                self.exec()
            self.getParent().read(self)
        return self

    def exec(self):
        if self._is_exec is False:
            self.getParent().execute(self)
            self._is_exec = True
            self._exec_time = time.time()
        return self

    def addData(self, data):
        self._data += data
        return self

    def getData(self):
        return self._data

    def getParsedData(self):
        return self._parse()

    def getReturnData(self):
        return self._remove_command()

    def setError(self, e):
        self._error = e
        self.setDone()
        return self

    def getError(self):
        return self._error

    def get(self, throw=True):
        self.exec()
        while True:
            self.getParent().read(self)
            if self.getIsDone(True) is False:
                time.sleep(0.01)  # this structure has to go (kept for parity with the original)
            elif self._error is None:
                return self.getParsedData()
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
