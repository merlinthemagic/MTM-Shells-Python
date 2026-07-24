
import fcntl
import os
import pty
import re
import shutil
import struct
import subprocess
import termios
import time

from .processing import Processing
from ..process_pipe import ProcessPipe


class Initialization(Processing):

	def __init__(self):
		self._reg_ex = None
		self._commit_chars = None
		self._use_sudo = False
		self._base_pipes = None
		super().__init__()

	def setSudo(self, use_sudo):
		self._use_sudo = use_sudo
		return self

	def getRegex(self):
		if self._reg_ex is None:
			self._reg_ex = "[bash." + os.urandom(8).hex() + "]"
		return self._reg_ex

	def getCommit(self):
		if self._commit_chars is None:
			self._commit_chars = chr(13)
		return self._commit_chars

	def initialize(self):
		if self._is_init is False and self._init_active is False:
			self._init_active = True
			try:
				# set the prompt to a known value
				str_cmd = 'PS1="' + self.getRegex() + '"'
				reg_ex = "(" + re.escape(self.getRegex()) + ")"

				r_tries = 10
				while True:
					try:
						self.getCmd(str_cmd, reg_ex).get()
						break  # success
					except Exception:
						if r_tries > 0:
							r_tries -= 1
							# system is a little busy, pipe not ready yet
							time.sleep(0.1)
							continue
						raise

				# ssh connections (and some ptys) won't inherit a sane
				# terminal width from the parent
				self.setTerminalSize(1000, 1000)

				# don't record a history for this session
				self.getCmd("unset HISTFILE").get()

				# disable bracketed paste for the current session
				self.getCmd("bind 'set enable-bracketed-paste 0'").get()

				# reset the output so we have a clean beginning
				self.getPipes().resetStdOut()

				self._is_init = True
				self._init_active = False
			except Exception:
				self._init_active = False
				raise

	def _get_base_pipes(self):
		if self._base_pipes is None:

			if self.getParent() is not None:
				raise RuntimeError("Has parent, cannot be base")
			elif self._is_term is True:
				raise RuntimeError("Cannot establish base pipes, shell terminated")
			elif self._term_active is True:
				raise RuntimeError("Cannot establish base pipes, shell is currently terminating")

			bash_path = shutil.which("bash")
			if bash_path is None:
				raise RuntimeError("Missing Bash application")

			if self._use_sudo is True:
				sudo_path = shutil.which("sudo")
				if sudo_path is None:
					raise RuntimeError("Missing sudo application")
				# requires passwordless sudo over bash, e.g. in /etc/sudoers:
				#   someuser ALL=(ALL) NOPASSWD:/bin/bash
				argv = [sudo_path, "-n", bash_path]
			else:
				argv = [bash_path]

			master_fd, slave_fd = pty.openpty()
			self._set_pty_size(master_fd, 1000, 1000)

			env = os.environ.copy()
			env["TERM"] = "vt100"

			try:
				process = subprocess.Popen(
					argv,
					stdin=slave_fd,
					stdout=slave_fd,
					stderr=slave_fd,
					env=env,
					preexec_fn=os.setsid,
					close_fds=True,
				)
			except Exception as e:
				os.close(master_fd)
				os.close(slave_fd)
				raise RuntimeError("Failed to execute shell setup: " + str(e))
			finally:
				# the child now owns the slave side
				try:
					os.close(slave_fd)
				except OSError:
					pass

			# make the master fd non-blocking so read() never stalls
			flags	= fcntl.fcntl(master_fd, fcntl.F_GETFL)
			fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

			self._base_pipes = ProcessPipe(master_fd, process)

		return self._base_pipes

	@staticmethod
	def _set_pty_size(fd, rows, cols):
		winsize = struct.pack("HHHH", rows, cols, 0, 0)
		fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
