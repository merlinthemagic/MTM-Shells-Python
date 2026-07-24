
import re

from .base import Base


class RouterOs(Base):

	def __init__(self):
		super().__init__()
		self._check_line = 0

	def _check_data(self):
		delim = self.getDelimitor()
		# we handle newlines as well via re.S (equivalent of PHP's /s modifier)
		if (
			delim
			and re.search("(.*)?(" + delim + ")", self.getData(), re.S) is not None  # too costly to check return data on every read, just do raw for starters
			and (self.getFindCommand() is False or self._cmd_found() is True)
			and re.search(delim, self.getReturnData(), re.S) is not None
		):
			self.setDone()

		if self.getIsDone() is False and self.getRunTime() > self.getTimeout():
			if not delim:
				# we wanted to read until time ran out
				self.setDone()
			else:
				self.setError(RuntimeError("RouterOS: Command read timeout"))

	def _parse(self):
		delim = self.getDelimitor()
		if delim and self.getError() is None:
			f_delim = None
			lines = list(reversed(self._remove_command(False)))
			for l_id, line in enumerate(lines):
				if line.startswith("[9999B"):
					# part of the VT100 ctrl sequence, VT100 because that is the bash base terminal
					# src: https://www.gnu.org/software/screen/manual/html_node/Control-Sequences.html
					line = line[6:]
				m = re.search("(.*)?(" + delim + ")", line, re.S)
				if m:
					group1 = m.group(1) or ""
					if group1.strip() == "":
						lines[l_id] = ""
					else:
						lines[l_id] = group1
					f_delim = l_id
				elif f_delim is not None:
					# we found the delimitor and this next line does not have another delimitor
					# time to stop
					break
			if f_delim is not None:
				lines = lines[f_delim + 1:]
			return "\n".join(reversed(lines))
		else:
			return self._remove_command(True)

	def _remove_command(self, as_str=True):
		str_cmd = self.getCmd()
		lines = self._get_lines()
		if str_cmd is not None and str_cmd.strip() != "":
			for l_key, line in enumerate(lines):
				# is the line part of the command?
				cmd_pos = line.rfind(str_cmd)
				if cmd_pos != -1:
					# this line holds all of the command
					lines = lines[l_key + 1:]
					line = line[cmd_pos + len(str_cmd):]
					if len(line.strip()) > 0:
						lines.insert(0, line)
					if len(lines) > 0 and lines[0].startswith("[K"):
						# in v6 each new command char results in a new line + break + "[K" + new char
						# dont trim anything else. If we do a blanket left trim we lose more than the command
						lines[0] = lines[0][2:]
					break
		if as_str is True:
			return "\n".join(lines)
		else:
			return lines

	def _cmd_found(self):
		str_cmd = ""
		cmd = self.getCmd()
		if cmd is not None:
			for ch in cmd:
				o = ord(ch)
				if 31 < o < 127:
					str_cmd += ch
		if str_cmd.strip() != "":
			lines = self._get_lines()
			for line in lines:
				if line.rfind(str_cmd) != -1:
					return True
		else:
			return True
		return False

	def _get_lines(self):
		r_data = []
		lines = self.getData().split("\x1B")
		for line in lines:
			output = ""
			for ch in line:
				o = ord(ch)
				if 31 < o < 127:
					output += ch
				elif o in (10, 13):
					r_data.append(output)
					output = ""
			r_data.append(output)
		return r_data
