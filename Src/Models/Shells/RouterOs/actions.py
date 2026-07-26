
import re

from .initialization import Initialization

class Actions(Initialization):

	_shell_type = "routeros"

	def getCmd(self, str_cmd=None, reg_exp=None, timeout=None):
		if self.getChild() is None:
			if self.isInit() is False:
				self.initialize()
			if self.isTerm() is True:
				raise RuntimeError("Cannot create command, shell is in terminated state")

			# local import: avoids a circular import between the Shells and
			# Commands packages (mirrors how the PHP autoloader resolves
			# \MTM\Shells\Models\Commands\RouterOs on demand)
			from ...Commands.routeros import RouterOs as _RouterOsCommand

			r_obj = _RouterOsCommand()
			r_obj.setParent(self).setCmd(str_cmd).setCommit(self.getCommit())
			if reg_exp is None:
				r_obj.setDelimitor(re.escape(self.getRegex()))
			else:
				r_obj.setDelimitor(reg_exp)
			if timeout is None:
				r_obj.setTimeout(self.getDefaultTimeout())
			else:
				r_obj.setTimeout(timeout)
			return r_obj
		else:
			return self.getChild().getCmd(str_cmd, reg_exp, timeout)

	def getPipes(self):
		p_obj = self.getParent()
		if p_obj is not None:
			return p_obj.getPipes()
		else:
			# happens if the shell was terminated and someone holds a command obj and executes after
			raise RuntimeError("Cannot get pipes shell has no parent")
