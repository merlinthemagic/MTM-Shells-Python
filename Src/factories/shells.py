"""
Mirrors Src/Factories/Shells.php

Only getBash() was ported (getRouterOs() lived here in the original but is
out of scope for this port).
"""
from .base import Base
from ..models.shells.bash.actions import Actions as _BashActions


class Shells(Base):
    def get_bash(self, use_sudo=False):
        """
        Returns an interactive bash shell object.

        use_sudo=True mirrors the PHP behaviour: it spawns `sudo -n bash`,
        which requires the calling user to have passwordless sudo rights
        over bash (see the original README's sudoers snippet).
        """
        r_obj = _BashActions()
        r_obj.set_sudo(use_sudo)
        return r_obj
