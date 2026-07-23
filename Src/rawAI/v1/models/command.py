"""
MTM_Shells/models/command.py

Mirrors MTM-Shells' Models/Commands/{Base,RouterOs}.php.

Represents a single command sent to a RouterOS shell: tracks the raw bytes
read back, and knows how to strip VT100 escape sequences, the echoed
command itself, and everything after the completion prompt, to hand back
just the meaningful output.

This is an internal/model class -- code using this package normally
interacts with tools.connection.RouterOSConnection instead of constructing
these directly (though get_cmd() on that class returns one of these, and
you can call .get() on it yourself for more control over timing/errors).
"""

import re
import time

from MTM_Shells.errors import RouterOSError


class RouterOSCommand:

    def __init__(self, connection, cmd, delimiter, timeout=25.0, find_command=True):
        self._connection = connection
        self._cmd = cmd
        self._delimiter = delimiter          # compiled regex marking "done"
        self._timeout = timeout              # seconds
        self._find_command = find_command    # False for e.g. password prompts
        self._data = ""                      # raw accumulated bytes (as str)
        self._is_exec = False
        self._is_done = False
        self._error = None
        self._start_time = None

    # -- basic accessors --------------------------------------------------

    @property
    def cmd(self):
        return self._cmd

    @property
    def data(self):
        """Raw, unparsed data read back so far."""
        return self._data

    @property
    def error(self):
        return self._error

    def is_done(self):
        return self._is_done

    def add_data(self, chunk):
        self._data += chunk

    def set_error(self, exc):
        self._error = exc
        self._is_done = True

    def set_done(self):
        self._is_done = True

    # -- execution ---------------------------------------------------------

    def exec(self):
        """Send the command to the shell. Idempotent."""
        if not self._is_exec:
            self._connection._write(self)
            self._is_exec = True
            self._start_time = time.monotonic()
        return self

    def _check_done(self):
        if self._is_done:
            return
        if self._delimiter is not None and self._delimiter.search(self._data):
            # Critical: the delimiter must match in the data *after* the
            # echoed command is stripped out, not just anywhere in the raw
            # buffer. RouterOS echoes back "[user@host] > <cmd>" right
            # after you send a command -- and that echoed line matches the
            # exact same prompt pattern used to detect completion. If we
            # only checked the raw buffer, we could decide "done" on the
            # echo itself, before the real output had even arrived over
            # the wire -- a timing-dependent race, not a deterministic bug.
            if (not self._find_command or self._cmd_echo_seen()) and \
                    self._delimiter.search(self.get_return_data()):
                self.set_done()
                return
        if self._start_time is not None and (time.monotonic() - self._start_time) > self._timeout:
            if self._delimiter is None:
                # We just wanted to read until time ran out.
                self.set_done()
            else:
                self.set_error(RouterOSError(f"Command read timeout: {self._cmd!r}"))

    def _cmd_echo_seen(self):
        """Loose equivalent of PHP's getCmdFound(): did we see the command
        we sent echoed back yet? Only meaningful text characters count."""
        if not self._cmd or not self._cmd.strip():
            return True
        printable_cmd = "".join(c for c in self._cmd if 31 < ord(c) < 127)
        printable_data = "".join(c for c in self._data if 31 < ord(c) < 127)
        return printable_cmd in printable_data

    def get(self, raise_on_error=True):
        """
        Block until the command completes (or times out), then return the
        cleaned output. Equivalent to PHP's Command::get().
        """
        self.exec()
        while True:
            self._connection._read(self)
            self._check_done()
            if self._is_done:
                if self._error is not None:
                    if raise_on_error:
                        raise self._error
                    return self._data
                return self._parse()
            time.sleep(0.01)

    def get_return_data(self):
        """Raw data with the echoed command line removed, but prompt/escape
        sequences left in -- used during login-flow parsing and completion
        detection."""
        return self._strip_echoed_command(self._data)

    # -- parsing / cleanup, ported from MTM-Shells RouterOs.php ------------

    def _strip_echoed_command(self, text):
        """Remove everything up to and including the echoed command."""
        if not self._cmd or not self._cmd.strip():
            return text
        idx = text.rfind(self._cmd)
        if idx == -1:
            return text
        remainder = text[idx + len(self._cmd):]
        # RouterOS v6-style "[K" erase-to-end-of-line right after the
        # command echo; strip it rather than losing surrounding content.
        if remainder.startswith("\x1b[K"):
            remainder = remainder[3:]
        return remainder

    def _get_lines(self):
        """
        Split raw data on ESC (\\x1B) the way RouterOs.php's getLines() does,
        keeping only printable characters per fragment and treating CR/LF as
        line breaks. This is what actually removes VT100 control sequences
        (cursor moves, color codes) rather than leaving them embedded in text.
        """
        lines = []
        for segment in self._data.split("\x1b"):
            current = ""
            for ch in segment:
                o = ord(ch)
                if 31 < o < 127:
                    current += ch
                elif o in (10, 13):
                    lines.append(current)
                    current = ""
            lines.append(current)
        return lines

    def _parse(self):
        """
        Full cleanup pass: strip escape sequences, drop the echoed command
        (which RouterOS/the pty echo *twice* -- local echo plus the
        remote shell's own echo -- so both must be skipped), and cut
        everything from the completion prompt onward. Mirrors
        RouterOs.php's parse().
        """
        if self._delimiter is None:
            return self._strip_echoed_command(self._data)

        lines = self._get_lines()

        if self._cmd and self._cmd.strip():
            printable_cmd = "".join(c for c in self._cmd if 31 < ord(c) < 127)
            last_echo_idx = None
            remainder = ""
            for i, line in enumerate(lines):
                if printable_cmd and printable_cmd in line:
                    pos = line.rfind(printable_cmd)
                    remainder = line[pos + len(printable_cmd):]
                    last_echo_idx = i
                elif last_echo_idx is not None:
                    break
            if last_echo_idx is not None:
                lines = lines[last_echo_idx + 1:]
                if remainder.strip():
                    lines.insert(0, remainder)
                if lines and lines[0].startswith("[K"):
                    lines[0] = lines[0][2:]

        # Walk from the end, keep lines up to (not including) the prompt.
        found_delim_at = None
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            if line.startswith("[9999B"):
                # VT100 cursor-position control sequence artifact.
                line = line[6:]
                lines[i] = line
            m = self._delimiter.search(line)
            if m:
                prefix = line[: m.start()]
                lines[i] = prefix if prefix.strip() else ""
                found_delim_at = i
            elif found_delim_at is not None:
                break

        if found_delim_at is not None:
            # Keep everything *before* the trailing prompt block, not after.
            lines = lines[:found_delim_at]

        return "\n".join(lines).strip("\n")
