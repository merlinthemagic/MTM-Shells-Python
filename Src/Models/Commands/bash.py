
import re

from .base import Base

class Bash(Base):

	def __init__(self):
		super().__init__()
		self._check_line = 0

	def _check_data(self):
		delim = self.getDelimitor()
		if delim:
			# we just want a hit, the order of the lines does not matter
			found = False
			lines = self.getData().split("\n")
			l_id = 0
			for l_id, line in enumerate(lines):
				if self._check_line <= l_id:
					if re.search("(.*)?(" + delim + ")", line):
						found = True
						break
			if found is False and l_id > 0:
				self._check_line = l_id - 1
			elif found is True:
				if re.search(delim, self.getReturnData(), re.S):
					self.setDone()

		if self.getIsDone() is False and self.getRunTime() > self.getTimeout():
			if not delim:
				# we wanted to read until time ran out
				self.setDone()
			else:
				self.setError(RuntimeError("Bash: Command read timeout"))

	def _parse(self):
		data = self._remove_command()
		delim = self.getDelimitor()
		lines = data.split("\n")
		if len(lines) > 0 and delim:
			# locate the delimiter in the return - faster to start from the bottom
			lines = list(reversed(lines))
			idx = 0
			while idx < len(lines):
				line = lines[idx]
				m = re.search("(.+)?(" + delim + ")", line)
				if m:
					group1 = m.group(1) or ""
					group2 = m.group(2) or ""
					if re.escape(self.getParent().getRegex()) != delim:
						# user supplied a custom regex: include both the data and the match
						lines[idx] = group1 + group2
					elif len(group1.strip()) > 0:
						# there is data before the default regex, keep that, discard the regex
						lines[idx] = group1
					else:
						# only the delimiter was on the last line
						del lines[idx]
					break
				else:
					# data that was picked up after the delimiter was reached
					del lines[idx]
					# don't advance idx - the list shifted, next element is now at idx
			lines = list(reversed(lines))
			data = "\n".join(lines)
		return data

	def _remove_command(self):
		# Command string removal from the returned data
		data = self.getData()
		str_cmd = self.getCmd()
		if str_cmd is not None:
			str_cmd = str_cmd.strip()
			lines = data.split("\n")
			if len(lines) > 0:

				parent = self.getParent()
				if parent.isInit() is True:
					# there could be leftover junk on the terminal before the
					# command was issued, so allow a longer string to match
					# before giving up
					term_width = parent.getTerminalSize(False)["width"]
					p_init = True
				else:
					term_width = None
					p_init = False

				cmd_len = len(self.getCmd().strip())
				max_len = cmd_len * 3
				remain_cmd = self.getCmd()
				cmd_line = ""
				result_lines = lines

				for l_key, line in enumerate(lines):

					if p_init is True and term_width is not None and len(line) >= term_width:
						# locate terminal breaks in very long, wrapped Commands
						o_index = 0
						c_index = 0
						n_line = ""
						c_chars = list(remain_cmd)
						o_chars = list(line)
						for c_char in c_chars:
							if o_index < len(o_chars):
								o_char = o_chars[o_index]
								if c_char != o_char:
									found = False
									for _ in range(4):
										o_index += 1
										if o_index >= len(o_chars):
											break
										o_char = o_chars[o_index]
										if c_char == o_char:
											found = True
											break
									if found is False:
										# failed to find a terminal break
										n_line = line
										break
							else:
								break
							n_line += o_char
							o_index += 1
							c_index += 1

						remain_cmd = remain_cmd[c_index:]
						line = n_line

					cmd_line += line.strip()
					cur_len = len(cmd_line)
					cmd_pos = cmd_len
					if str_cmd != "":
						pos = cmd_line.find(str_cmd)
						cmd_pos += pos if pos >= 0 else 0
					if cur_len == cmd_pos:
						# found the command; drop the lines up to and including it
						result_lines = lines[l_key + 1:]
						break
					elif cur_len > max_len:
						# no match
						result_lines = lines
						break

				data = "\n".join(result_lines)
		return data
