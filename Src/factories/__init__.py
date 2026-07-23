"""
Mirrors Src/Factories.php

USE: obj = Factories.get_shells().get_bash()

Note: the original also exposed getFiles()/getTools()/getStencils() for the
SFTP/SCP/Rsync tools and Su/Sudo stencils. Those were intentionally left out
of this port since it's scoped to interactive-shell + command execution only.
"""
from .shells import Shells as _Shells


class Factories:
    _s = {}

    @classmethod
    def get_shells(cls):
        if "get_shells" not in cls._s:
            cls._s["get_shells"] = _Shells()
        return cls._s["get_shells"]
