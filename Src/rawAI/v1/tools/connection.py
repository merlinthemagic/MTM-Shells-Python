"""
MTM_Shells/tools/connection.py

Mirrors MTM-SSH's Tools/Shells/RouterOs/Actions.php -- the public-facing
object ($ctrlObj in the PHP library) that ties together the raw shell
transport, the login flow, and prompt establishment, and exposes the
get_cmd()/exec() API used to actually run commands.
"""

import re
import time

from MTM_Shells.models.shell import RouterOSShell
from MTM_Shells.models.command import RouterOSCommand
from MTM_Shells.tools.password_authentication import (
    PasswordAuthentication,
    TERMINAL_SUFFIX,
)
from MTM_Shells.errors import RouterOSError


class RouterOSConnection:
    """
    Manages a single SSH session to a RouterOS device and lets you run
    arbitrary commands against it.

        with RouterOSConnection(host, "admin", "secret", port=1122) as conn:
            print(conn.exec("/interface/print"))
    """

    def __init__(self, host, username, password, port=22, connect_timeout=30.0,
                 debug_log=None):
        self._host = host
        self._raw_username = username
        self._password = password
        self._port = port
        self._connect_timeout = connect_timeout

        self._shell = None
        self._prompt_re = None  # compiled once we know the device identity
        self._is_connected = False

        # Optional path to a file that every raw chunk read from the pty
        # gets appended to immediately (flushed each write), so it can be
        # tailed live in a second session while a script runs -- purely a
        # debugging aid, no effect on parsing/behavior.
        self._debug_fh = open(debug_log, "a", buffering=1) if debug_log else None

    # -- I/O hooks used by RouterOSCommand ---------------------------------
    # (RouterOSCommand calls back into whatever object it's given via
    # ._write()/._read() -- here that's this connection, which just
    # delegates to the underlying shell transport and taps the debug log.)

    def _write(self, cmd_obj):
        self._shell.write(cmd_obj)

    def _read(self, cmd_obj):
        before = len(cmd_obj.data)
        self._shell.read(cmd_obj)
        if self._debug_fh is not None and len(cmd_obj.data) > before:
            self._debug_fh.write(repr(cmd_obj.data[before:]) + "\n")

    # -- connection lifecycle ----------------------------------------------

    def connect(self):
        if self._is_connected:
            return self

        username_with_suffix = f"{self._raw_username}{TERMINAL_SUFFIX}"
        self._shell = RouterOSShell(
            self._host, username_with_suffix, port=self._port,
            connect_timeout=self._connect_timeout,
        ).open()

        try:
            PasswordAuthentication(
                self._shell, self._raw_username, self._password,
                timeout=self._connect_timeout,
            ).login()
            self._establish_prompt()
        except Exception:
            self.close()
            raise

        self._is_connected = True
        return self

    def _establish_prompt(self):
        """
        Lock in the exact prompt regex for this device and clear any
        buffered junk, mirroring Initialization::resetDefaultRegEx()/
        resetPrompt().
        """
        self._prompt_re = re.compile(
            rf"\[{re.escape(self._raw_username)}@(.+?)\]\s*>\s*"
        )
        # Send a harmless command and consume its response to make sure
        # we're starting from a clean buffer before the caller's first
        # real command.
        self.get_cmd(':put ""').get(raise_on_error=False)

    def close(self):
        if self._shell is not None and self._shell.is_open():
            # /quit terminates the session -- RouterOS never sends a
            # completion prompt back for it, so routing this through the
            # normal Command polling loop just burns its full timeout
            # waiting for something that will never arrive. Best-effort
            # fire-and-forget instead: write it, give it a brief moment
            # to be sent, then close regardless.
            try:
                self._shell.raw_write(b"/quit\r")
                time.sleep(0.2)
            except OSError:
                pass
            self._shell.terminate()
        if self._debug_fh is not None:
            self._debug_fh.close()
            self._debug_fh = None
        self._is_connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # -- public command API -------------------------------------------------

    def get_cmd(self, cmd, timeout=25.0):
        """Build (but do not yet send) a RouterOSCommand against this
        connection's established prompt -- mirrors $ctrlObj->getCmd()."""
        if self._prompt_re is None:
            raise RouterOSError("Connection not established yet")
        return RouterOSCommand(self, cmd, self._prompt_re, timeout=timeout)

    def exec(self, cmd, timeout=25.0):
        """Convenience one-shot: send a command and return its cleaned
        output. Equivalent to $ctrlObj->getCmd($cmd)->exec()->get()."""
        return self.get_cmd(cmd, timeout=timeout).get()
