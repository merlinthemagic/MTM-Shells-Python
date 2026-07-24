
import re

from ..base import Base


class Termination(Base):

	def _issue_sig_int(self, throw=True):
		# SIGINT the current process and get the prompt back
		str_cmd = chr(3)
		self.getCmd(str_cmd).get(throw)

	def isBaseTerm(self):
		# figure out if the base pipes are still there
		return self.getParent().isBaseTerm()

	def terminate(self):
		if self._is_term is False and self._term_active is False:
			self._term_active = True
			try:
				if self._is_init is True:

					if self.getChild() is not None:
						self.getChild().terminate()

					# throwing during shutdown is still a problem
					if self.isBaseTerm() is False:

						# make sure the last command is dead
						self._issue_sig_int(False)
						cmd_obj = self.getCmd()
						str_cmd = "/quit"
						reg_ex = None
						timeout = 0
						if self.getParent() is not None:
							reg_ex = "(" + re.escape(self.getParent().getRegex()) + ")"
							timeout = cmd_obj.getTimeout()
						cmd_obj.setCmd(str_cmd).setDelimitor(reg_ex).setTimeout(timeout)
						cmd_obj.get(False)

				p_obj = self.getParent()
				if p_obj is not None:
					p_obj.setChild(None)
					self.setParent(None)

					if p_obj.getParent() is None:
						# below us is a base shell setup just to facilitate this shell
						p_obj.terminate()
			finally:
				self._is_term = True
				self._term_active = False

	def exceptHandler(self, e):
		pass
