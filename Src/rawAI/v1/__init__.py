"""
MTM_Shells

Python port of the RouterOS-relevant parts of merlinthemagic/MTM-SSH and
merlinthemagic/MTM-Shells: SSH into a RouterOS device and execute arbitrary
commands, with clean (escape-sequence-free, command-echo-free) return data.

    from MTM_Shells import RouterOSConnection

    with RouterOSConnection("10.127.17.1", "admin", "merlin", port=1122) as conn:
        print(conn.exec("/interface/print"))

Package layout mirrors MTM-SSH's own Models/Tools split:
    models/   -- internal state & mechanics (command parsing, raw pty transport)
    tools/    -- the public-facing classes you actually construct and call
    errors.py -- exceptions
"""

from MTM_Shells.tools.connection import RouterOSConnection
from MTM_Shells.models.command import RouterOSCommand
from MTM_Shells.errors import RouterOSError
from MTM_Shells.factories import Factories

__all__ = ["RouterOSConnection", "RouterOSCommand", "RouterOSError", "Factories"]
