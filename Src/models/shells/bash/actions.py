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

    def get_cmd(self, str_cmd=None, reg_exp=None, timeout=None):
        if self.get_child() is None:
            if self.is_init() is False:
                self.initialize()
            if self.is_term() is True:
                raise RuntimeError("Cannot create command, shell is in terminated state")

            # local import: avoids a circular import between the shells and
            # commands packages (mirrors how the PHP autoloader resolves
            # \MTM\Shells\Models\Commands\Bash on demand)
            from ...commands.bash import Bash as _BashCommand

            r_obj = _BashCommand()
            r_obj.set_parent(self).set_cmd(str_cmd).set_commit(self.get_commit())
            if reg_exp is None:
                r_obj.set_delimitor(re.escape(self.get_regex()))
            else:
                r_obj.set_delimitor(reg_exp)
            if timeout is None:
                r_obj.set_timeout(self.get_default_timeout())
            else:
                r_obj.set_timeout(timeout)
            return r_obj
        else:
            return self.get_child().get_cmd(str_cmd, reg_exp, timeout)

    def set_terminal_size(self, height, width):
        self.get_cmd("stty cols {} rows {}".format(width, height)).get()
        sz = self.get_terminal_size(True)
        if sz["height"] != height or sz["width"] != width:
            raise RuntimeError("Failed to set Terminal size")

    def get_terminal_size(self, refresh=True):
        if refresh is True or self._term_height is None or self._term_width is None:
            data = self.get_cmd("stty size").get()
            m = re.search(r"([0-9]+)\s([0-9]+)", data)
            if m:
                self._term_height = int(m.group(1))
                self._term_width = int(m.group(2))
            else:
                raise RuntimeError("Failed to get Terminal size")
        return {"height": self._term_height, "width": self._term_width}

    def get_temp_directory(self):
        tmp_dirs = ["/tmp/", "/dev/shm/"]
        home_dir = self.get_cmd("echo $HOME").get().strip()
        if home_dir != "":
            tmp_dirs.append(home_dir.rstrip("/") + "/")
        for tmp_dir in tmp_dirs:
            str_cmd = 'if [ -w "{0}" ]; then echo "isWrite"; else echo "noWrite"; fi'.format(tmp_dir)
            data = self.get_cmd(str_cmd).get().strip()
            if data == "isWrite":
                return tmp_dir
        raise RuntimeError("Failed to get temp directory")

    def get_max_input(self, refresh=False):
        if refresh is True or self._max_input is None:
            data = self.get_cmd("getconf ARG_MAX").get()
            m = re.search(r"([0-9]+)", data)
            if m:
                self._max_input = int(m.group(1))
            else:
                raise RuntimeError("Failed to get max input length")
        return self._max_input

    def get_pipes(self):
        if self.get_parent() is None:
            return self._get_base_pipes()
        else:
            return self.get_parent().get_pipes()
