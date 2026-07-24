
##Keep byte cache in temp location to avoid disk wear on IoT devices with eeproms or 
import sys
sys.pycache_prefix = "/tmp/pycache"

from .Facts import Facts

__all__ = ["Facts"]
