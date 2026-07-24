from .base import Base
from ..Models.Shells.Bash.actions import Actions as _BashActions
from ..Models.Shells.RouterOs.actions import Actions as _RouterOsActions

class Shells(Base):
	def getBash(self, use_sudo=False):
		r_obj = _BashActions()
		r_obj.setSudo(use_sudo)
		return r_obj

	def getRouterOs(self):
		r_obj = _RouterOsActions()
		return r_obj