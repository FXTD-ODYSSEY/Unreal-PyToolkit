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


def alert(msg=u"msg", title=u"警告",icon=QtWidgets.QMessageBox.Warning,button_text=u"确定"):
    # NOTE 生成 Qt 警告窗口
    msg_box = QtWidgets.QMessageBox()
    msg_box.setIcon(icon)
    msg_box.setWindowTitle(title)
    msg_box.setText(msg)
    msg_box.addButton(button_text, QtWidgets.QMessageBox.AcceptRole)
    unreal.parent_external_window_to_slate(msg_box.winId())
    dayu_theme.apply(msg_box)
    msg_box.exec_()