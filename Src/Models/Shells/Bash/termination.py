
import os
import re
import signal

from ..base import Base


class Termination(Base):

	def _issue_sig_int(self, throw=True, timeout=None):
		# Writing chr(3) (Ctrl+C) through the pty is picked up by the tty
		# line discipline and turned into a real SIGINT for the foreground
		# process group - same trick the PHP original used.
		cmd_obj = self.getCmd(chr(3))
		if timeout is not None:
			cmd_obj.setTimeout(timeout)
		cmd_obj.get(throw)

	def _issue_sig_quit(self, throw=True, timeout=None):
		cmd_obj = self.getCmd(chr(28))
		if timeout is not None:
			cmd_obj.setTimeout(timeout)
		cmd_obj.get(throw)

	def _pid_running(self):
		base_pipes = getattr(self, "_base_pipes", None)
		if base_pipes is None:
			return False
		return base_pipes.getProcess().poll() is None

	def isBaseTerm(self):
		# Figure out whether the base pipes / spawned bash process are still alive.
		if self.getParent() is not None:
			return self.getParent().isBaseTerm()

		if self._is_term is False and self._term_active is False:
			if self._pid_running():
				return False
		return True

	def terminate(self):
		if self._is_term is False and self._term_active is False:
			self._term_active = True
			try:
				if self._is_init is True:

					if self.getChild() is not None:
						self.getChild().terminate()

					if self.getParent() is None:
						# this is the base (root) shell
						if self._pid_running():
							# make sure the last command is dead, give it one
							# second - we don't care if it exits cleanly, we
							# are shutting the whole shell down regardless
							self._issue_sig_int(False, 1000)

							cmd_obj = self.getCmd()
							cmd_obj.setCmd("exit").setDelimitor(None).setTimeout(0)
							cmd_obj.get(False)

							base_pipes = getattr(self, "_base_pipes", None)
							proc = base_pipes.getProcess() if base_pipes else None
							if proc is not None:
								try:
									proc.wait(timeout=2)
								except Exception:
									try:
										os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
									except Exception:
										pass

						base_pipes = getattr(self, "_base_pipes", None)
						if base_pipes is not None:
							base_pipes.close()
						self._base_pipes = None

					elif self.is_base_term() is False:
						# this is a nested shell (e.g. a su/sudo elevation) -
						# exit back out to the parent shell's prompt
						self._issue_sig_int(False)

						cmd_obj = self.getCmd()
						reg_ex = "(" + re.escape(self.get_parent().get_regex()) + ")"
						timeout = cmd_obj.getTimeout()
						cmd_obj.setCmd("exit").setDelimitor(reg_ex).setTimeout(timeout)
						cmd_obj.get(False)

						self.getParent().setChild(None)
						self.setParent(None)
			finally:
				self._is_term = True
				self._term_active = False
