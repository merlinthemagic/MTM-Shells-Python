"""
Mirrors Src/Models/Shells/ProcessPipe.php

The PHP original wrote to / read from plain files on disk (stdIn as a named
FIFO, stdOut/stdErr as regular files), hand-tracking byte offsets, because
PHP had to shell out to a detached `python3 -c "pty.spawn(...)"` process to
get a pty at all. Since this port *is* Python, we skip that indirection and
talk to a real pty master file descriptor directly - it behaves like a
terminal: writes go to the child's stdin, and a read returns whatever new
output the child has produced (stdout+stderr combined, like a real terminal
session). No manual offset bookkeeping is required.
"""
import os


class ProcessPipe:

    def __init__(self, master_fd, process):
        self._master_fd = master_fd
        self._process = process  # subprocess.Popen handle for the spawned bash
        self._lock = True        # kept for API parity with the PHP lock file

    def getLock(self):
        return self._lock

    def setLock(self, val):
        self._lock = val
        return self

    def getProcess(self):
        return self._process

    def getMasterFd(self):
        return self._master_fd

    def write(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8", errors="replace")
        os.write(self._master_fd, data)
        return self

    def read(self):
        """Non-blocking read of whatever new output is currently available."""
        chunks = []
        try:
            while True:
                data = os.read(self._master_fd, 65536)
                if not data:
                    break
                chunks.append(data)
        except BlockingIOError:
            pass
        except OSError:
            # fd closed / process gone -> mirrors the PHP "pipe went away" case
            raise RuntimeError("stdOut went away")
        return b"".join(chunks).decode("utf-8", errors="replace")

    def resetStdOut(self):
        """
        Discards any output currently sitting unread in the pty buffer (e.g.
        leftover bytes from a command that timed out before we finished
        reading its output). The PHP original did this by fast-forwarding a
        byte offset into a backing file; since our read() has no backing
        file to seek in, we instead drain and throw away whatever is
        currently pending so the next real read() starts clean.
        """
        try:
            while True:
                data = os.read(self._master_fd, 65536)
                if not data:
                    break
        except BlockingIOError:
            pass
        except OSError:
            pass
        return self

    def close(self):
        try:
            os.close(self._master_fd)
        except OSError:
            pass
