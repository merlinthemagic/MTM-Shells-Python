"""
mtm_shells
==========

Python port of the interactive-shell portion of merlinthemagic/MTM-Shells
(https://github.com/merlinthemagic/MTM-Shells).

The original PHP library is much larger (SFTP/SCP/Rsync file tools, RouterOS
support, Su/Sudo "stencils", etc). This port focuses only on the piece that
was asked for: getting an interactive bash shell and executing commands
against it. The class/folder layout mirrors the original as closely as
Python's import system allows:

    PHP                                       Python
    ---------------------------------------   --------------------------------------------
    Src/Factories.php                         mtm_shells/factories/__init__.py  (Factories)
    Src/Factories/Base.php                    mtm_shells/factories/base.py      (Base)
    Src/Factories/Shells.php                  mtm_shells/factories/shells.py    (Shells)
    Src/Models/Shells/Base.php                mtm_shells/models/shells/base.py           (Base)
    Src/Models/Shells/ProcessPipe.php         mtm_shells/models/shells/process_pipe.py   (ProcessPipe)
    Src/Models/Shells/Bash/Termination.php    mtm_shells/models/shells/bash/termination.py    (Termination)
    Src/Models/Shells/Bash/Processing.php     mtm_shells/models/shells/bash/processing.py     (Processing)
    Src/Models/Shells/Bash/Initialization.php mtm_shells/models/shells/bash/initialization.py (Initialization)
    Src/Models/Shells/Bash/Actions.php        mtm_shells/models/shells/bash/actions.py        (Actions)
    Src/Models/Commands/Base.php              mtm_shells/models/commands/base.py  (Base)
    Src/Models/Commands/Bash.php              mtm_shells/models/commands/bash.py  (Bash)

The one unavoidable deviation: PHP can have both a `Factories.php` file and a
`Factories/` folder side by side (its autoloader resolves classes by full
path). Python's import system can't have a module and a package of the same
name in the same parent package, so the `Factories` class itself now lives in
`factories/__init__.py` instead of a sibling `factories.py` file.

Usage:

    from mtm_shells import Factories

    shell = Factories.get_shells().get_bash()
    print(shell.get_cmd("whoami").get())
    shell.terminate()
"""
from .factories import Factories

__all__ = ["Factories"]
