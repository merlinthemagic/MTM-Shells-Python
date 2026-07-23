"""
Mirrors Src/Models/Shells/Bash/Processing.php
"""
from .termination import Termination


class Processing(Termination):

    def execute(self, cmd_obj):
        if self.get_child() is None:
            if cmd_obj.get_cmd() is not None:
                # None means "just keep reading" - don't discard buffered output
                self.get_pipes().reset_std_out()
            self.write(cmd_obj)
            return self
        else:
            return self.get_child().execute(cmd_obj)

    def write(self, cmd_obj):
        if self.get_parent() is None:
            self._raw_write(cmd_obj)
        else:
            self.get_parent().write(cmd_obj)

    def read(self, cmd_obj):
        if self.get_parent() is None:
            self._raw_read(cmd_obj)
        else:
            self.get_parent().read(cmd_obj)

    def _raw_write(self, cmd_obj):
        cmd_obj.set_running()
        if cmd_obj.get_cmd() is not None:
            try:
                exe_cmd = cmd_obj.get_cmd() + cmd_obj.get_commit()
                self.get_pipes().write(exe_cmd)
            except Exception:
                # stdIn went away - not sure if the remote side is responsible
                cmd_obj.set_error(RuntimeError("Shell was terminated"))
                self.terminate()

    def _raw_read(self, cmd_obj):
        try:
            data = self.get_pipes().read()
            if data != "":
                cmd_obj.add_data(data)
        except RuntimeError:
            # stdOut went away - not sure if the remote side is responsible
            cmd_obj.set_error(RuntimeError("Shell was terminated"))
            self.terminate()
