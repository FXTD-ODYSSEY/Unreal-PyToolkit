#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Import local modules
from dayu_path.base import DayuPath


class DayuPathPlugin(object):
    @classmethod
    def register_func(cls, func):
        try:
            if type(func) is type(lambda : 1) and not hasattr(DayuPath,
                                                              func.__name__):
                setattr(DayuPath, func.__name__, func)
                return True
            else:
                return False
        except:
            return False

    @classmethod
    def register_attribute(cls, key, default_value=None):
        try:
            if isinstance(key, str) and not hasattr(DayuPath, key):
                setattr(DayuPath, key, default_value)
                return True
            else:
                return False
        except:
            return False

    @classmethod
    def unregister(cls, key):
        try:
            if isinstance(key, str) and hasattr(DayuPath, key):
                delattr(DayuPath, key)
                return True
            else:
                return False
        except:
            return False
