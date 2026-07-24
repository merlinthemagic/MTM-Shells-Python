#!/usr/bin/env python3
import sys
import os
import argparse
import importlib.util

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
	"MTM_Shells",
	os.path.join(_pkg_dir, "__init__.py"),
	submodule_search_locations=[_pkg_dir],
)
MTM_Shells = importlib.util.module_from_spec(_spec)
sys.modules["MTM_Shells"] = MTM_Shells
_spec.loader.exec_module(MTM_Shells)

Facts = MTM_Shells.Facts


if __name__ == "__main__":
	try:
		Facts.getTest().execute()
	except Exception as e:
		print("Test failed:", e, file=sys.stderr)
		sys.exit(1)