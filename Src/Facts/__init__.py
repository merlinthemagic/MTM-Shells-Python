from .shells import Shells as _Shells
from .test import Test as _Test

class Facts:
	
	_s = {}

	@classmethod
	def getShells(cls):
		key		= "getShells";
		if key not in cls._s:
			cls._s[key] = _Shells();
		return cls._s[key];

	@classmethod
	def getTest(cls):
		key		= "getTest";
		if key not in cls._s:
			cls._s[key] = _Test();
		return cls._s[key];