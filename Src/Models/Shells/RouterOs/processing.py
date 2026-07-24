
import re
import time
import uuid

from .termination import Termination


class Processing(Termination):

	def execute(self, cmd_obj):
		if self.getChild() is None:
			self.getPipes().resetStdOut()
			self.write(cmd_obj)
			return self
		else:
			return self.getChild().execute(cmd_obj)

	def write(self, cmd_obj):
		# cannot be a base shell
		if self.isInit() is True or self._init_active is True:
			self.getParent().write(cmd_obj)
		else:
			raise RuntimeError("Cannot write. Shell not initialized")

	def read(self, cmd_obj):
		# cannot be a base shell
		if self.isInit() is True or self._init_active is True:
			self.getParent().read(cmd_obj)
		else:
			raise RuntimeError("Cannot read. Shell not initialized")

	def resetPrompt(self, timeout=10000):
		# keeps looping until we have a clean prompt
		# for unknown reasons the prompt is sometimes written more than once
		# that means a command will be issued, but the reader will catch an old prompt and return
		# either the previous data or more likely an empty return.
		t_time = time.time() + (timeout / 1000)

		# chop the total timeout into smaller chunks so we get at least a few tries
		# provide at least 2500 ms to complete
		p_time = timeout / 3
		if p_time < 2500:
			p_time = timeout

		i = 0
		while True:
			i += 1
			pattern = "cleaner." + uuid.uuid4().hex
			str_cmd = ':put "' + pattern + '";'
			reg_ex = "(" + pattern + ")([B9\\r\\n\\x1b\\[]+?)(" + re.escape(self.getRegex()) + ")"
			cmd_obj = self.getCmd(str_cmd, reg_ex, p_time)
			cmd_obj.get(False)  # may timeout

			if cmd_obj.getError() is None:
				return
			elif t_time < time.time():
				raise RuntimeError("Failed to recover prompt")
			else:
				# wait for output to clear, sleep longer and longer or we just clog the pipe on slow connections
				if i == 1:
					time.sleep(0.25)
				elif i == 2:
					time.sleep(0.5)
				elif i == 3:
					time.sleep(0.75)
				else:
					time.sleep(1)
