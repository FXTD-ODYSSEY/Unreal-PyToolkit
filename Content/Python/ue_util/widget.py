# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-07-21 19:23:46'

import unreal
from Qt import QtCore, QtWidgets, QtGui
from dayu_widgets import dayu_theme
from dayu_widgets.toast import MToast
from dayu_widgets.combo_box import MComboBox
from dayu_widgets.mixin import property_mixin, cursor_mixin, focus_shadow_mixin

def alert(msg=u"msg", title=u"警告", icon=QtWidgets.QMessageBox.Warning, button_text=u"确定"):
    # NOTE 生成 Qt 警告窗口
    msg_box = QtWidgets.QMessageBox()
    msg_box.setIcon(icon)
    msg_box.setWindowTitle(title)
    msg_box.setText(msg)
    msg_box.addButton(button_text, QtWidgets.QMessageBox.AcceptRole)
    unreal.parent_external_window_to_slate(msg_box.winId())
    dayu_theme.apply(msg_box)
    msg_box.exec_()


toast_dict = {
    "error": MToast.error,
    "info": MToast.info,
    "success": MToast.success,
    "warning": MToast.warning,
}

def toast(text="", typ=""):
    # NOTE 获取鼠标的位置弹出屏幕居中的 MToast 警告
    global MESSAGE_TOAST
    MESSAGE_TOAST = QtWidgets.QWidget()
    pos = QtGui.QCursor.pos()
    desktop = QtWidgets.QApplication.desktop()
    MESSAGE_TOAST.setGeometry(desktop.screenGeometry(pos))
    toast_dict.get(typ,MToast.error)(parent=MESSAGE_TOAST, text=text)

def ui_PyInit(widget):
    if not hasattr(widget,"children"):
        return

    # NOTE 初始化 PyInit 中配置的方法
    data = widget.property("PyInit")
    if data:
        try:
            data = json.loads(data,object_pairs_hook=OrderedDict)
            for method,param in data['method'].items():
                param = param if isinstance(param,list) else [param]
                getattr(widget,method)(*param)
        except:
            pass

    for child in widget.children():
        ui_PyInit(child)