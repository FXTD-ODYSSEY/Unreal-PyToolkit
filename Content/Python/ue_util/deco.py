# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-08-11 19:21:27'


from .widget import alert

def error_log(func):
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            return res
        except:
            import traceback
            alert(u"程序错误 | 请联系 梁伟添 timmyliang\n\n%s" % traceback.format_exc())

    return wrapper