# -*- coding: utf-8 -*-
"""
初始化 unreal Qt 环境
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-05-30 21:47:47'

from Qt import QtCore, QtWidgets, QtGui
import os
import sys
import json
import unreal
from functools import partial
from collections import OrderedDict
from dayu_widgets import dayu_theme

DIR = os.path.dirname(__file__)

# TODO git 自动 pull | SVN 自动更新

type_map = {
    "command": unreal.ToolMenuStringCommandType.COMMAND,
    "python": unreal.ToolMenuStringCommandType.PYTHON
}

def read_menu_json(path):

    with open(path, 'r') as f:
        data = json.load(f, object_pairs_hook=OrderedDict, encoding='utf-8')

    menu_section_dict = data['section']
    menu_entry_dict = data['menu']
    for menu, data in menu_entry_dict.items():
        data['type'] = type_map[data['type'].lower()]
        data['command'] = data['command'].format(Content=DIR)

    return menu_section_dict, menu_entry_dict


def create_menu():
    # NOTE 读取 menu json 配置
    menu_section_dict, menu_entry_dict = read_menu_json("%s/menu.json" % DIR)

    # NOTE https://forums.unrealengine.com/development-discussion/python-scripting/1767113-making-menus-in-py
    menus = unreal.ToolMenus.get()

    # NOTE 获取主界面的主菜单位置
    main_menu = menus.find_menu("LevelEditor.MainMenu")
    if not main_menu:
        raise RuntimeError(
            "Failed to find the 'Main' menu. Something is wrong in the force!")

    # NOTE 添加一个下拉菜单
    script_menu = main_menu.add_sub_menu(
        main_menu.get_name(), "PythonTools", "Tools", "PyToolkit")

    # NOTE 初始化下拉菜单的 Section 分组
    for section, label in menu_section_dict.items():
        script_menu.add_section(section, label)

    # NOTE 根据 json 来配置菜单显示的 Entry
    for menu, data in menu_entry_dict.items():
        entry = unreal.ToolMenuEntry(
            name=menu,
            type=unreal.MultiBlockType.MENU_ENTRY,
            insert_position=unreal.ToolMenuInsert(
                "", unreal.ToolMenuInsertType.FIRST)
        )
        entry.set_label(data.get('label', "untitle"))
        command = data.get('command', '')
        entry.set_string_command(data.get("type", 0), "", string=command)
        script_menu.add_menu_entry(data.get('section', ''), entry)

    # NOTE 刷新组件
    menus.refresh_all_widgets()


def slate_deco(func):
    def wrapper(self, single=True, *args, **kwargs):
        # NOTE 只保留一个当前类窗口
        if single:
            for win in QtWidgets.QApplication.topLevelWidgets():
                if win is self:
                    continue
                elif self.__class__.__name__ in str(type(win)):
                    win.deleteLater()
                    # win.setParent(None)
                    win.close()

        # NOTE https://forums.unrealengine.com/unreal-engine/unreal-studio/1526501-how-to-get-the-main-window-of-the-editor-to-parent-qt-or-pyside-application-to-it
        # NOTE 让窗口嵌入到 unreal 内部
        unreal.parent_external_window_to_slate(self.winId())
        # NOTE 添加 dayu_widget 的样式
        res = func(self, *args, **kwargs)
        dayu_theme.apply(self)
        return res
    return wrapper


# This function will receive the tick from Unreal
def __QtAppTick__(delta_seconds):
    pass
    # TODO 不添加事件处理 Qt 的窗口运行正常 | 添加反而会让 imgui 失去焦点
    # QtWidgets.QApplication.processEvents()
    # # NOTE 处理 deleteDeferred 事件
    # QtWidgets.QApplication.sendPostedEvents()


# This part is for the initial setup. Need to run once to spawn the application.
unreal_app = QtWidgets.QApplication.instance()
if not unreal_app:
    unreal_app = QtWidgets.QApplication([])
    tick_handle = unreal.register_slate_post_tick_callback(__QtAppTick__)
    __QtAppQuit__ = partial(
        unreal.unregister_slate_post_tick_callback, tick_handle)
    unreal_app.aboutToQuit.connect(__QtAppQuit__)

    with open(os.path.join(DIR,"main.css"),'r') as f:
        unreal_app.setStyleSheet(f.read())

    # NOTE 重载 show 方法
    QtWidgets.QWidget.show = slate_deco(QtWidgets.QWidget.show)

    create_menu()
