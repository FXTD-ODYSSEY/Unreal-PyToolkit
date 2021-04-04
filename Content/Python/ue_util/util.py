# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-08-28 08:52:34'


import os
import unreal

sys_lib = unreal.SystemLibrary()

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
    
def unreal_progress(tasks,label =u"进度",total=None):
    total = total if total else len(tasks)
    with unreal.ScopedSlowTask(total, label) as task:
        task.make_dialog(True)
        for i, item in enumerate(tasks):
            if task.should_cancel():
                break
            task.enter_progress_frame(1, "%s %s/%s" % (label,i, total))
            yield i, item
            
def convert_to_filename(path):
    content = sys_lib.get_project_content_directory()
    path = path.replace("/Game/", content)
    path = os.path.abspath(path).replace("\\", "/")
    if os.path.isdir(path):
        return path
    path = os.path.splitext(path)[0]
    return "%s.uasset" % path