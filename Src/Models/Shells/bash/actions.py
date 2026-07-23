"""
Mirrors Src/Models/Shells/Bash/Actions.php
"""
import re

from .initialization import Initialization


class Actions(Initialization):

    _shell_type = "bash"

    def __init__(self):
        self._term_height = None
        self._term_width = None
        self._max_input = None
        super().__init__()

    def getCmd(self, str_cmd=None, reg_exp=None, timeout=None):
        if self.getChild() is None:
            if self.isInit() is False:
                self.initialize()
            if self.isTerm() is True:
                raise RuntimeError("Cannot create command, shell is in terminated state")

            # local import: avoids a circular import between the Shells and
            # Commands packages (mirrors how the PHP autoloader resolves
            # \MTM\Shells\Models\Commands\Bash on demand)
            from ...Commands.bash import Bash as _BashCommand

            r_obj = _BashCommand()
            r_obj.setParent(self).setCmd(str_cmd).setCommit(self.getCommit())
            if reg_exp is None:
                r_obj.setDelimitor(re.escape(self.getRegex()))
            else:
                r_obj.setDelimitor(reg_exp)
            if timeout is None:
                r_obj.setTimeout(self.getDefaultTimeout())
            else:
                r_obj.setTimeout(timeout)
            return r_obj
        else:
            return self.getChild().getCmd(str_cmd, reg_exp, timeout)

    def setTerminalSize(self, height, width):
        self.getCmd("stty cols {} rows {}".format(width, height)).get()
        sz = self.getTerminalSize(True)
        if sz["height"] != height or sz["width"] != width:
            raise RuntimeError("Failed to set Terminal size")

    def getTerminalSize(self, refresh=True):
        if refresh is True or self._term_height is None or self._term_width is None:
            data = self.getCmd("stty size").get()
            m = re.search(r"([0-9]+)\s([0-9]+)", data)
            if m:
                self._term_height = int(m.group(1))
                self._term_width = int(m.group(2))
            else:
                raise RuntimeError("Failed to get Terminal size")
        return {"height": self._term_height, "width": self._term_width}

    def getTempDirectory(self):
        tmp_dirs = ["/tmp/", "/dev/shm/"]
        home_dir = self.getCmd("echo $HOME").get().strip()
        if home_dir != "":
            tmp_dirs.append(home_dir.rstrip("/") + "/")
        for tmp_dir in tmp_dirs:
            str_cmd = 'if [ -w "{0}" ]; then echo "isWrite"; else echo "noWrite"; fi'.format(tmp_dir)
            data = self.getCmd(str_cmd).get().strip()
            if data == "isWrite":
                return tmp_dir
        raise RuntimeError("Failed to get temp directory")

    def getMaxInput(self, refresh=False):
        if refresh is True or self._max_input is None:
            data = self.getCmd("getconf ARG_MAX").get()
            m = re.search(r"([0-9]+)", data)
            if m:
                self._max_input = int(m.group(1))
            else:
                raise RuntimeError("Failed to get max input length")
        return self._max_input

    def getPipes(self):
        if self.getParent() is None:
            return self._get_base_pipes()
        else:
            return self.getParent().getPipes()
