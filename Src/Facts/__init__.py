from .shells import Shells as _Shells
from .test import Test as _Test


class Facts:
    _s = {}

    @classmethod
    def getShells(cls):
        if "getShells" not in cls._s:
            cls._s["getShells"] = _Shells()
        return cls._s["getShells"]

    @classmethod
    def getTest(cls):
        if "getTest" not in cls._s:
            cls._s["getTest"] = _Test()
        return cls._s["getTest"]