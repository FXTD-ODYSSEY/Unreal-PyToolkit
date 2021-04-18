# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-08-11 19:21:27'

import inspect
from functools import wraps, update_wrapper
from .widget import alert

def error_log(*_args, **_kwargs):
    static = _kwargs.get("static")
    def wrapper(func):
        if inspect.isclass(func):

            @wraps(func)
            def cls_wrapper(cls):
                # NOTE 如果是 class 接管所有 func
                for name, member in inspect.getmembers(cls, inspect.isfunction):
                    bound_value = cls.__dict__.get(name)
                    is_static = isinstance(bound_value, staticmethod)
                    setattr(cls, name, error_log(static=is_static)(member))
                return cls

            return cls_wrapper(func)

        elif callable(func):

            @wraps(func)
            def func_wrapper(*args, **kwargs):
                if static:
                    args = args[1:]
                try:
                    res = func(*args, **kwargs)
                    return res
                except:
                    import traceback

                    traceback.print_exc()
                    alert(u"程序错误 | 请联系 梁伟添 timmyliang\n\n%s" % traceback.format_exc())

            return func_wrapper

    # NOTE 判断是否是直接装饰了
    if len(_args) == 1:
        func = _args[0]
        return wrapper(func)
    else:
        return wrapper