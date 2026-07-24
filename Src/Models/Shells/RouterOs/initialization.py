
import re

from .processing import Processing


class Initialization(Processing):

	def __init__(self):
		self._reg_ex = None
		self._commit_chars = None
		super().__init__()

	def getRegex(self):
		return self._reg_ex

	def resetDefaultRegEx(self):
		self._reg_ex = None
		str_cmd = " "
		reg_ex = r"\]\s+\>(\s*)?$"
		self.getCmd(str_cmd, reg_ex).get()

		str_cmd = ':local MHIT "";'
		reg_chars = r"[a-zA-Z0-9\+\_\-\.\:\#\,]+"
		reg_ex = r"\[((" + reg_chars + r")@(" + reg_chars + r"))\]\s+\>"
		cmd_obj = self.getCmd(str_cmd, reg_ex)
		cmd_obj.get()
		data = cmd_obj.getReturnData()
		lines = [line for line in data.split("\n") if line != ""]
		for line in lines:
			t_line = line.strip()
			m = re.search(r"(\[((" + reg_chars + r")@(" + reg_chars + r"))]\s+\>)", t_line)
			if m:
				self._reg_ex = m.group(1)
				break
		return self._reg_ex

	def getCommit(self):
		if self._commit_chars is None:
			self._commit_chars = chr(13)
		return self._commit_chars

	def initialize(self):
		if self._is_init is False and self._init_active is False:
			self._init_active = True
			try:
				# need the ability to reset the shell delimitor regEx
				# if we change the identity of the device, the prompt changes too

				if self.resetDefaultRegEx() is None:
					raise RuntimeError("Failed to get shell prompt")

				# reset the output so we have a clean beginning
				self.resetPrompt()
				self.getPipes().resetStdOut()

				# fully initialized
				self._is_init = True
				self._init_active = False

			except Exception:
				self._init_active = False
				raise
