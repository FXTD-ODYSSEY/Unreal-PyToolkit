# -*- coding: utf-8 -*-
"""
Initialize unreal Qt Environment
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2020-05-30 21:47:47"

import os
import sys
import json
import time
import codecs
import platform
import posixpath
import traceback
import subprocess
from subprocess import PIPE, Popen
from threading import Thread
from functools import partial
from collections import OrderedDict, defaultdict

startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = subprocess.SW_HIDE

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty  # python 2.x

import unreal

DIR = os.path.dirname(__file__)
CONTENT = os.path.dirname(DIR)
CONFIG = os.path.join(CONTENT, "_config")
VENDOR = os.path.join(CONTENT, "_vendor")
PYTHON = os.path.join(CONTENT, "Python")

def can_import(module):
    try:
        __import__(module)
    except ImportError:
        return False
    return True


def read_json(json_path):
    import codecs

    try:
        with codecs.open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f, object_pairs_hook=OrderedDict)
    except:
        import traceback

        traceback.print_exc()
        data = {}
    return data

def read_config_json(config):
    return read_json(os.path.join(CONFIG, "%s.json" % config))

def add_vendor_path():
    config_path = os.path.join(VENDOR, "vendor.json")
    vendor = read_json(config_path)
    version = "py%s" % sys.version[:3]
    module_data = defaultdict(list)
    for package, collections in vendor.items():
        module = collections.get("module")
        package_folder = os.path.join(VENDOR, package)
        for f in collections.get("folders", {}):
            path = os.path.join(package_folder, f)
            module_data[module].append(os.path.abspath(path))
        if [k for k in collections if k.startswith("py")]:
            collections = collections.get(version)
            if collections:
                for f in collections.get("folders", {}):
                    path = os.path.join(package_folder, f)
                    module_data[module].append(os.path.abspath(path))

    for module, paths in module_data.items():
        if not can_import(module):
            sys.path.extend(paths)

add_vendor_path()

from Qt import QtCore, QtWidgets, QtGui
from dayu_widgets import dayu_theme
import six

sys_lib = unreal.SystemLibrary

menus = unreal.ToolMenus.get()

FORMAT_ARGS = {"Content": CONTENT}

COMMAND_TYPE = {
    "COMMAND": unreal.ToolMenuStringCommandType.COMMAND,
    "PYTHON": unreal.ToolMenuStringCommandType.PYTHON,
    "CUSTOM": unreal.ToolMenuStringCommandType.CUSTOM,
}

INSERT_TYPE = {
    "AFTER": unreal.ToolMenuInsertType.AFTER,
    "BEFORE": unreal.ToolMenuInsertType.BEFORE,
    "DEFAULT": unreal.ToolMenuInsertType.DEFAULT,
    "FIRST": unreal.ToolMenuInsertType.FIRST,
}

MENU_TYPE = {
    "BUTTON_ROW": unreal.MultiBoxType.BUTTON_ROW,
    "MENU": unreal.MultiBoxType.MENU,
    "MENU_BAR": unreal.MultiBoxType.MENU_BAR,
    "TOOL_BAR": unreal.MultiBoxType.TOOL_BAR,
    "UNIFORM_TOOL_BAR": unreal.MultiBoxType.UNIFORM_TOOL_BAR,
    "VERTICAL_TOOL_BAR": unreal.MultiBoxType.VERTICAL_TOOL_BAR,
}

ENTRY_TYPE = {
    "BUTTON_ROW": unreal.MultiBlockType.BUTTON_ROW,
    "EDITABLE_TEXT": unreal.MultiBlockType.EDITABLE_TEXT,
    "HEADING": unreal.MultiBlockType.HEADING,
    "MENU_ENTRY": unreal.MultiBlockType.MENU_ENTRY,
    "NONE": unreal.MultiBlockType.NONE,
    "TOOL_BAR_BUTTON": unreal.MultiBlockType.TOOL_BAR_BUTTON,
    "TOOL_BAR_COMBO_BUTTON": unreal.MultiBlockType.TOOL_BAR_COMBO_BUTTON,
    "WIDGET": unreal.MultiBlockType.WIDGET,
}

ACTION_TYPE = {
    "BUTTON": unreal.UserInterfaceActionType.BUTTON,
    "CHECK": unreal.UserInterfaceActionType.CHECK,
    "COLLAPSED_BUTTON": unreal.UserInterfaceActionType.COLLAPSED_BUTTON,
    "NONE": unreal.UserInterfaceActionType.NONE,
    "RADIO_BUTTON": unreal.UserInterfaceActionType.RADIO_BUTTON,
    "TOGGLE_BUTTON": unreal.UserInterfaceActionType.TOGGLE_BUTTON,
}


def handle_menu(data):
    """
    handle_menu recursive menu generation
    """
    menu = data.get("menu")
    if not menu:
        return

    for section, config in data.get("section", {}).items():
        config = config if isinstance(config, dict) else {"label": config}
        config.setdefault("label", "untitle")
        insert = INSERT_TYPE.get(config.get("insert_type", "").upper())
        if insert:
            config["insert_type"] = insert
        insert_name = config.get("insert_name")
        config["insert_name"] = insert_name if insert_name else "None"
        menu.add_section(section, **config)

    for prop, value in data.get("property", {}).items():
        if prop == "menu_owner" or value == "":
            continue
        elif prop == "menu_type":
            value = MENU_TYPE.get(value.upper())
        menu.set_editor_property(prop, value)

    for entry_name, config in data.get("entry", {}).items():
        prop = config.get("property", {})

        for k, v in prop.items():
            prop.pop("owner") if not prop.get("owner") is None else None
            prop.pop("script_object") if not prop.get("script_object") is None else None

            if v == "":
                prop.pop(k)
            elif k == "insert_position":
                position = INSERT_TYPE.get(v.get("position", "").upper())
                v["position"] = (
                    position if position else unreal.ToolMenuInsertType.FIRST
                )
                v["name"] = v.get("name", "")
                prop[k] = unreal.ToolMenuInsert(**v)
            elif k == "type":
                typ = ENTRY_TYPE.get(str(v).upper())
                prop[k] = typ if typ else unreal.MultiBlockType.MENU_ENTRY
            elif k == "user_interface_action_type":
                typ = ACTION_TYPE.get(str(v).upper())
                prop.update({k: typ}) if typ else prop.pop(k)

        prop.setdefault("name", entry_name)
        prop.setdefault("type", unreal.MultiBlockType.MENU_ENTRY)
        entry = unreal.ToolMenuEntry(**prop)
        tooltip = config.get("tooltip")
        entry.set_tool_tip(tooltip) if tooltip else None

        entry.set_label(config.get("label", "untitle"))
        typ = COMMAND_TYPE.get(config.get("type", "").upper(), 0)

        command = config.get("command", "").format(**FORMAT_ARGS)
        entry.set_string_command(typ, "", string=command)
        menu.add_menu_entry(config.get("section", ""), entry)

    for entry_name, config in data.get("sub_menu", {}).items():
        init = config.get("init", {})
        owner = menu.get_name()
        section_name = init.get("section", "")
        name = init.get("name", entry_name)
        label = init.get("label", "")
        tooltip = init.get("tooltip", "")
        sub_menu = menu.add_sub_menu(owner, section_name, name, label, tooltip)
        config.setdefault("menu", sub_menu)
        handle_menu(config)

def create_menu():
    # NOTE Read menu json settings
    menu_json = read_config_json("menu")
    fail_menus = {}
    # NOTE https://forums.unrealengine.com/development-discussion/python-scripting/1767113-making-menus-in-py
    for tool_menu, config in menu_json.items():
        menu = menus.find_menu(tool_menu)
        if not menu:
            fail_menus.update({tool_menu: config})
            continue
        config.setdefault("menu", menu)
        handle_menu(config)

    menus.refresh_all_widgets()

    return fail_menus


def register_BP():
    path = os.path.join(CONTENT, "BP")
    if not os.path.isdir(path):
        return
    for root, _, files in os.walk(path):
        for f in files:
            if not f.endswith(".py"):
                continue
            command = 'py "%s"' % posixpath.join(root, f).replace("\\", "/")
            unreal.SystemLibrary.execute_console_command(None, command)

def slate_deco(func):
    def wrapper(self, single=True, *args, **kwargs):
        if single:
            # TODO crash 
            for win in QtWidgets.QApplication.allWidgets():
                if win is self:
                    continue
                elif self.__class__.__name__ in str(type(win)):
                    win.deleteLater()
                    win.close()

        res = func(self, *args, **kwargs)
        # NOTE https://forums.unrealengine.com/unreal-engine/unreal-studio/1526501-how-to-get-the-main-window-of-the-editor-to-parent-qt-or-pyside-application-to-it
        unreal.parent_external_window_to_slate(self.winId())
        dayu_theme.apply(self)
        return res

    return wrapper



if __name__ == "__main__":

    # NOTE This part is for the initial setup. Need to run once to spawn the application.
    unreal_app = QtWidgets.QApplication.instance()

    if not unreal_app:
        unreal_app = QtWidgets.QApplication([])

        def __QtAppTick__(delta_seconds):
            QtWidgets.QApplication.sendPostedEvents()

        tick_handle = unreal.register_slate_post_tick_callback(__QtAppTick__)
        __QtAppQuit__ = partial(unreal.unregister_slate_post_tick_callback, tick_handle)
        unreal_app.aboutToQuit.connect(__QtAppQuit__)

        # NOTE override show method
        QtWidgets.QWidget.show = slate_deco(QtWidgets.QWidget.show)

    with open(os.path.join(CONFIG, "main.css"), "r") as f:
        unreal_app.setStyleSheet(f.read())

    fail_menus = create_menu()
    if fail_menus:
        global __tick_menu_elapsed__
        __tick_menu_elapsed__ = 0

        def timer_add_menu(menu_dict, delta):
            global __tick_menu_elapsed__
            __tick_menu_elapsed__ += delta

            # NOTE avoid frequently executing
            if __tick_menu_elapsed__ < 0.5:
                return

            __tick_menu_elapsed__ = 0

            # NOTE all menu added the clear the tick callback
            if not menu_dict:
                global __py_add_menu_tick__
                unreal.unregister_slate_post_tick_callback(__py_add_menu_tick__)
                return

            flag = False
            menu_list = []
            for tool_menu, config in menu_dict.items():
                menu = menus.find_menu(tool_menu)
                if not menu:
                    continue
                menu_list.append(tool_menu)
                flag = True
                config.setdefault("menu", menu)
                handle_menu(config)

            if flag:
                [menu_dict.pop(m) for m in menu_list]
                menus.refresh_all_widgets()

        # NOTE register custom menu
        callback = partial(timer_add_menu, fail_menus)
        global __py_add_menu_tick__
        __py_add_menu_tick__ = unreal.register_slate_post_tick_callback(callback)
        __QtAppQuit__ = partial(
            unreal.unregister_slate_post_tick_callback, __py_add_menu_tick__
        )
        unreal_app.aboutToQuit.connect(__QtAppQuit__)

    setting = read_config_json("setting")

    if setting.get("blueprint"):
        register_BP()

    hotkey_enabled = setting.get("hotkey")
    if hotkey_enabled:
        os_config = {
            "Windows": "Win64",
            "Linux": "Linux",
            "Darwin": "Mac",
        }
        os_platform = os_config.get(platform.system())
        if not os_platform:
            raise OSError("Unsupported platform '{}'".format(platform.system()))

        PYTHON = "Python" if six.PY2 else "Python3"
        ThirdParty = os.path.join(sys.executable, "..", "..", "ThirdParty")
        interpreter = os.path.join(ThirdParty, PYTHON, os_platform, "python.exe")
        interpreter = os.path.abspath(interpreter)

        exec_file = os.path.join(CONTENT, "_key_listener", "__listener__.py")
        msg = "lost path \n%s\n%s" % (interpreter, exec_file)
        assert os.path.exists(interpreter) and os.path.exists(exec_file), msg

        # NOTE spawn a Python process for keyboard listening
        # NOTE https://stackoverflow.com/a/4896288
        ON_POSIX = "posix" in sys.builtin_module_names
        p = Popen(
            [interpreter, exec_file],
            shell=False,
            stdout=PIPE,
            stderr=PIPE,
            bufsize=1,
            close_fds=ON_POSIX,
            startupinfo=startupinfo,
        )
        unreal_app.aboutToQuit.connect(p.terminate)

        def enqueue_output(p, queue):
            for line in iter(p.stdout.readline, b""):
                queue.put(line)
            p.stdout.close()

        q = Queue()
        t = Thread(target=enqueue_output, args=(p, q))
        t.daemon = True  # thread dies with the program
        t.start()

        hotkey_config = read_config_json("hotkey")

        callbacks = {
            "COMMAND": lambda command: sys_lib.execute_console_command(None, command),
            "PYTHON": lambda command: eval(command),
        }

        def get_foreground_window_pid():
            from ctypes import wintypes, windll, byref

            # NOTE https://stackoverflow.com/a/56572696
            h_wnd = windll.user32.GetForegroundWindow()
            pid = wintypes.DWORD()
            windll.user32.GetWindowThreadProcessId(h_wnd, byref(pid))
            return pid.value

        def __hotkey_tick__(delta_seconds):
            try:
                line = q.get_nowait()
            except Empty:
                return

            if not line or delta_seconds > 0.1:
                return

            if platform.system() == "Windows":
                pid = get_foreground_window_pid()
                if pid != os.getpid():
                    return

            # line = str(line.strip(), "utf-8")
            line = line.strip() if six.PY2 else str(line.strip(), "utf-8")
            config = hotkey_config.get(line)
            if not config:
                return

            typ = config.get("type", "").upper()
            callback = callbacks.get(typ)
            if not callback:
                return

            command = config.get("command", "").format(**FORMAT_ARGS)
            callback(command)

        tick_handle = unreal.register_slate_post_tick_callback(__hotkey_tick__)
        __QtAppQuit__ = partial(unreal.unregister_slate_post_tick_callback, tick_handle)
        unreal_app.aboutToQuit.connect(__QtAppQuit__)
