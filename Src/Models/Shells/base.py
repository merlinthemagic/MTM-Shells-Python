"""
Mirrors Src/Models/Shells/Base.php
"""
import atexit
import uuid


class Base:

    _shell_type = None

    def __init__(self):
        if type(self) is Base:
            # PHP declares this class `abstract`; Python has no direct
            # equivalent so we enforce it at construction time instead.
            raise TypeError("Base is abstract and cannot be instantiated directly")

        self._guid = None
        self._parent_obj = None    # shell that this instance is built on top of
        self._child_obj = None     # shell built on top of this instance
        self._cmd_obj = None       # currently executing command
        self._d_timeout = 25000    # default command timeout, in ms
        self._is_init = False      # shell has been fully set up
        self._is_term = False      # shell is terminated
        self._init_active = False  # init is in progress
        self._term_active = False  # termination is in progress

        # __del__ is not guaranteed to run on interpreter/process teardown
        # (e.g. os._exit, unhandled signals). PHP's register_shutdown_function
        # exists for the same reason; atexit is the Python equivalent.
        atexit.register(self._atexit_terminate)

    def _atexit_terminate(self):
        try:
            self.terminate()
        except Exception:
            pass

    def __del__(self):
        try:
            self.terminate()
        except Exception:
            pass

    def get_guid(self):
        if self._guid is None:
            self._guid = str(uuid.uuid4())
        return self._guid

    def get_type(self):
        return self._shell_type

    def is_init(self):
        return self._is_init

    def is_term(self):
        return self._is_term

    def set_child(self, obj):
        self._child_obj = obj
        return self

    def get_child(self):
        return self._child_obj

    def set_parent(self, obj):
        self._parent_obj = obj
        return self

    def get_parent(self):
        return self._parent_obj

    def set_default_timeout(self, ms):
        self._d_timeout = ms
        return self

    def get_default_timeout(self):
        return self._d_timeout

    def terminate(self):
        raise NotImplementedError

    def get_cmd(self, str_cmd=None, reg_exp=None, timeout=None):
        raise NotImplementedError
