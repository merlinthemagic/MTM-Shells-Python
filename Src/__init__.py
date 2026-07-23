
##Keep byte cache in temp location to avoid disk wear on IoT 
import sys
sys.pycache_prefix = "/tmp/pycache"

from .Facts import Facts

__all__ = ["Facts"]
