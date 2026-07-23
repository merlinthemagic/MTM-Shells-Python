# mtm_shells (Python port)

A Python 3 port of the interactive-bash-shell part of
[merlinthemagic/MTM-Shells](https://github.com/merlinthemagic/MTM-Shells).

Only the piece needed to **get an interactive bash shell and execute
commands against it** was ported. Left out of scope (present in the PHP
original but not here): RouterOS shells, the SFTP/SCP/Rsync file tools, and
the Su/Sudo "stencils".

## Class / folder layout

The Python package mirrors the original PHP `Src/` tree as closely as
Python's import system allows:

| PHP | Python |
|---|---|
| `Src/Factories.php` (class `Factories`) | `mtm_shells/factories/__init__.py` |
| `Src/Factories/Base.php` | `mtm_shells/factories/base.py` |
| `Src/Factories/Shells.php` | `mtm_shells/factories/shells.py` |
| `Src/Models/Shells/Base.php` | `mtm_shells/models/shells/base.py` |
| `Src/Models/Shells/ProcessPipe.php` | `mtm_shells/models/shells/process_pipe.py` |
| `Src/Models/Shells/Bash/Termination.php` | `mtm_shells/models/shells/bash/termination.py` |
| `Src/Models/Shells/Bash/Processing.php` | `mtm_shells/models/shells/bash/processing.py` |
| `Src/Models/Shells/Bash/Initialization.php` | `mtm_shells/models/shells/bash/initialization.py` |
| `Src/Models/Shells/Bash/Actions.php` | `mtm_shells/models/shells/bash/actions.py` |
| `Src/Models/Commands/Base.php` | `mtm_shells/models/commands/base.py` |
| `Src/Models/Commands/Bash.php` | `mtm_shells/models/commands/bash.py` |

The class hierarchy is identical too: `Actions -> Initialization ->
Processing -> Termination -> Base` for shells, `Bash -> Base` for commands.

The one unavoidable difference: PHP can have a `Factories.php` file and a
sibling `Factories/` folder at the same time (its autoloader resolves by
full class path). Python can't have a module and a package share a name in
the same parent package, so the `Factories` class itself lives in
`factories/__init__.py` rather than a `factories.py` file next to a
`factories/` folder.

## Key implementation difference (and why)

The PHP library had to shell out to a **detached** `python3 -c
"pty.spawn(['bash'])"` process, wired up through hand-rolled named-pipe/FIFO
files on disk with manually-tracked byte offsets, plus a whole guard-process
scheme (grepping `/proc`, spawning a `nohup`'d watchdog) to clean up the
shell if PHP crashed uncleanly. That entire apparatus existed because PHP
has no built-in way to allocate a pty.

Since this port *is* Python, it uses the stdlib `pty` module directly:
`pty.openpty()` gives a master/slave fd pair, and `subprocess.Popen` attaches
`bash` (or `sudo -n bash`) to the slave side. Reads/writes go straight to the
master fd (non-blocking). This removes the on-disk files, the offset
bookkeeping, and the watchdog process entirely, while keeping the exact same
public API (`get_cmd()`, `.get()`, prompt-based delimiter matching, terminal
size handling, timeouts, `terminate()`, nested-shell support, etc.).
Cleanup-on-crash is handled by `atexit` / `__del__`, Python's equivalent of
PHP's `register_shutdown_function` + `__destruct`.

Sudo elevation (`get_bash(True)`) now runs `sudo -n bash` directly rather
than `sudo -n python3`, so your sudoers entry should grant NOPASSWD on
`bash`, e.g.:

```
someuser ALL=(ALL) NOPASSWD:/bin/bash
```

## Usage

```python
from mtm_shells import Factories

# bash as the current user
shell = Factories.get_shells().get_bash()

print(shell.get_cmd("whoami").get())          # webserver user, or root if you got a root shell

shell.get_cmd("cd /var").get()                # enter the /var directory
data = shell.get_cmd("ls -sho --color=none").get()
print(data)                                   # directory listing from /var

shell.terminate()
```

### Bash as root

```python
# via passwordless sudo (see sudoers note above)
shell = Factories.get_shells().get_bash(True)
print(shell.get_cmd("whoami").get())          # root
```

### Custom timeouts / prompt matching

```python
cmd = shell.get_cmd("sleep 5 && echo done", None, 2000)  # 2000ms timeout
try:
    print(cmd.get())
except Exception as e:
    print("timed out:", e)
```

## Requirements

- Linux (relies on `pty`, `fcntl`, `termios`, process groups - same as the
  original, which was Linux-only).
- `bash` on `PATH`.
- Python 3.7+, standard library only - no third-party dependencies.
