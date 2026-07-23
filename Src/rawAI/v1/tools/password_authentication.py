"""
MTM_Shells/tools/password_authentication.py

Mirrors MTM-SSH's Tools/Shells/{Bash,RouterOs}/PasswordAuthentication.php --
this is the "bash spawns ssh directly, then handles the RouterOS password
login prompts" version (as opposed to the *other* PasswordAuthentication.php
in the PHP lib, which jumps from an already-open RouterOS shell to a second
device via `/system ssh` -- that chained/"Destination" variant isn't
ported here since it wasn't needed).
"""

import re
import time

from MTM_Shells.errors import RouterOSError
from MTM_Shells.models.command import RouterOSCommand

# RouterOS username suffix: disables console colors, disables terminal
# capability probing ("dumb" mode), and sets a wide/tall terminal so
# output doesn't get mid-word wrapped or polluted with escape sequences.
TERMINAL_SUFFIX = "+cet400w50h"


class PasswordAuthentication:
    """Drives the login prompt sequence for a freshly-opened RouterOSShell,
    stopping once the real RouterOS command prompt is reached."""

    def __init__(self, shell, raw_username, password, timeout=30.0):
        self._shell = shell
        self._raw_username = raw_username
        self._password = password
        self._timeout = timeout

    def login(self):
        patterns = {
            "password": re.compile(r"[Pp]assword:"),
            "license": re.compile(r"Do you want to see the software license\?"),
            "remove_config": re.compile(r"remove it, you will be disconnected\."),
            "routeros_prompt": re.compile(rf"\[{re.escape(self._raw_username)}@(.+?)\]\s*>"),
            "new_password": re.compile(r"[Nn]ew password>"),
            "error": re.compile(
                r"Could not resolve hostname|Connection reset by peer|"
                r"Connection timed out|Permission denied|"
                r"Connection closed by remote host|Connection refused|No route to host"
            ),
        }
        combined = re.compile("|".join(p.pattern for p in patterns.values()))

        step = RouterOSCommand(self._shell, "", combined, timeout=self._timeout, find_command=False)
        result = self._wait_for_any(step, patterns)

        if result == "password":
            step = RouterOSCommand(self._shell, self._password, combined,
                                    timeout=self._timeout, find_command=False)
            result = self._wait_for_any(step, patterns)

        # RouterOS may show a license prompt and/or a "remove default
        # config" prompt before dropping you at the real shell prompt.
        # Answer "n" to each and keep re-checking.
        while result in ("license", "remove_config", "new_password"):
            if result == "new_password":
                answer = chr(3)  # Ctrl-C: decline the forced password change
            else:
                answer = "n"
            step = RouterOSCommand(self._shell, answer, combined,
                                    timeout=self._timeout, find_command=False)
            result = self._wait_for_any(step, patterns)

        if result == "error":
            raise RouterOSError(f"SSH connection error: {step.data!r}")
        if result != "routeros_prompt":
            raise RouterOSError(f"Unexpected login state ({result!r}): {step.data!r}")

    def _wait_for_any(self, cmd_obj, patterns):
        """Drive one login step until one of the named patterns matches."""
        cmd_obj.exec()
        deadline = time.monotonic() + self._timeout
        while True:
            self._shell.read(cmd_obj)
            for name, pattern in patterns.items():
                if pattern.search(cmd_obj.data):
                    return name
            if time.monotonic() > deadline:
                raise RouterOSError(f"Timed out during login: {cmd_obj.data!r}")
            time.sleep(0.01)
