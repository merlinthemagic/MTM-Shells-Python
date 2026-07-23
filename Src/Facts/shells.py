from .base import Base
from ..Models.Shells.bash.actions import Actions as _BashActions

class Shells(Base):
    def getBash(self, use_sudo=False):
        r_obj = _BashActions()
        r_obj.setSudo(use_sudo)
        return r_obj
