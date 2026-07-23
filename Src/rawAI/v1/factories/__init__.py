"""
MTM_Shells/factories/__init__.py

Mirrors MTM-SSH's Factories.php: a cached, "static-feeling" entry point
that hands out factory objects.

    from MTM_Shells import Factories

    conn = Factories.get_shells().password_authentication(
        "10.127.17.1", "admin", "merlin", port=1122
    )
    cmd = conn.get_cmd("/interface/print")
    data = cmd.get()
    print(data)

Python has no direct equivalent of PHP's `private static $_cStore` +
static methods, but a classmethod backed by a class-level cache dict
reproduces the same behavior: the first call builds a Shells instance,
every subsequent call returns the same cached one.
"""

from MTM_Shells.factories.shells import Shells


class Factories:
    _cache = {}

    @classmethod
    def get_shells(cls):
        if "shells" not in cls._cache:
            cls._cache["shells"] = Shells()
        return cls._cache["shells"]
