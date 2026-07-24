
from .termination import Termination


class Processing(Termination):

	def execute(self, cmd_obj):
		if self.getChild() is None:
			if cmd_obj.getCmd() is not None:
				# None means "just keep reading" - don't discard buffered output
				self.getPipes().resetStdOut()
			self.write(cmd_obj)
			return self
		else:
			return self.getChild().execute(cmd_obj)

	def write(self, cmd_obj):
		if self.getParent() is None:
			self._raw_write(cmd_obj)
		else:
			self.getParent().write(cmd_obj)

	def read(self, cmd_obj):
		if self.getParent() is None:
			self._raw_read(cmd_obj)
		else:
			self.getParent().read(cmd_obj)

	def _raw_write(self, cmd_obj):
		cmd_obj.setRunning()
		if cmd_obj.getCmd() is not None:
			try:
				exe_cmd = cmd_obj.getCmd() + cmd_obj.getCommit()
				self.getPipes().write(exe_cmd)
			except RuntimeError as e:
				# stdIn went away - not sure if the remote side is responsible
				cmd_obj.setError(RuntimeError("Shell was terminated", 44733))
				self.terminate()

	def _raw_read(self, cmd_obj):
		try:
			data = self.getPipes().read()
			if data != "":
				cmd_obj.addData(data)
		except RuntimeError as e:
			# stdOut went away - not sure if the remote side is responsible
			##TODO: figure out how to get the error. e.g. on SSH login with a wrong password
			##the file is removed and rather than a meaningful error e.g. Permission denied
			##we just push the below generic exception upstream
			cmd_obj.setError(RuntimeError("Shell was terminated", 44734))
			self.terminate()
