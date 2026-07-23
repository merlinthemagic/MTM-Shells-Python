"""
MTM_Shells/models/shell.py

Mirrors MTM-Shells' Models/Shells/Base.php + RouterOs/{Processing,Termination}.php.

Owns the actual pty + spawned `ssh` process: opening it, writing bytes to
it, and pulling whatever's currently available to read. This is the raw
transport -- it knows nothing about RouterOS prompts, login flows, or
command parsing; that lives in models/command.py and tools/.
"""

import os
import pty
import select


class RouterOSShell:

    def __init__(self, host, username, port=22, connect_timeout=30.0):
        self._host = host
        self._username = username
        self._port = port
        self._connect_timeout = connect_timeout

        self._master_fd = None
        self._proc = None

    def open(self):
        """Fork a pty and exec `ssh` into the child, giving it a real
        terminal (this is what makes the RouterOS console behave sanely --
        the same reason a raw subprocess.Popen() with plain pipes behaves
        differently than a real tty)."""
        ssh_args = [
            "ssh",
            "-p", str(self._port),
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "StrictHostKeyChecking=no",
            "-o", "GSSAPIAuthentication=no",
            "-o", "NumberOfPasswordPrompts=1",
            "-o", f"ConnectTimeout={int(self._connect_timeout)}",
            f"{self._username}@{self._host}",
        ]

        pid, master_fd = pty.fork()
        if pid == 0:
            # child
            os.execvp("ssh", ssh_args)
            os._exit(1)  # only reached if execvp fails

        self._master_fd = master_fd
        self._proc = pid
        return self

    def is_open(self):
        return self._master_fd is not None

    def write(self, cmd_obj):
        text = cmd_obj.cmd
        if text is None:
            return
        os.write(self._master_fd, text.encode("utf-8", errors="replace") + b"\r")

    def read(self, cmd_obj, chunk_size=65536, poll_timeout=0.2):
        """Non-blocking-ish read: pull whatever is available right now."""
        ready, _, _ = select.select([self._master_fd], [], [], poll_timeout)
        if self._master_fd in ready:
            try:
                chunk = os.read(self._master_fd, chunk_size)
            except OSError:
                chunk = b""
            if chunk:
                cmd_obj.add_data(chunk.decode("utf-8", errors="replace"))

    def raw_write(self, data: bytes):
        """Write raw bytes directly, bypassing the Command machinery --
        used for the fire-and-forget /quit on close()."""
        os.write(self._master_fd, data)

    def terminate(self):
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None
        if self._proc:
            try:
                os.waitpid(self._proc, os.WNOHANG)
            except ChildProcessError:
                pass
            self._proc = None
