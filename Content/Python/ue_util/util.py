# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-08-28 08:52:34'


import unreal


def list_menu(num=1000):
    menu_list = set()
    for i in range(num):
        obj = unreal.find_object(None,"/Engine/Transient.ToolMenus_0:ToolMenu_%s" % i)
        if not obj:
            continue
        menu_name = str(obj.menu_name)
        if menu_name != "None":
            menu_list.add(menu_name)
    return list(menu_list)
    
