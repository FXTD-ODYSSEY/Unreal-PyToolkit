# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-07-30 20:11:42'


import os
import re
import sys
import unreal

from Qt import QtCore, QtGui, QtWidgets
from Qt import QtCompat

# GUI
class Launcher(QtWidgets.QWidget):

    """A menu to find and execute Maya commands and user scripts."""

    def __init__(self, *args, **kwds):
        super(Launcher, self).__init__(*args, **kwds)

        DIR,file_name = os.path.split(__file__)
        base_name,_ = os.path.splitext(file_name)
        ui_path = os.path.join(DIR,"%s.ui" % base_name)
        QtCompat.loadUi(ui_path,self)

        # NOTE 设置图标
        style = QtWidgets.QApplication.style()
        pixmap = style.standardPixmap(QtWidgets.QStyle.SP_FileDialogContentsView)
        self.Label.setPixmap(pixmap)

        # TODO 设置状态标签

        self.setWindowFlags(QtCore.Qt.Popup|QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # self.setFlags(QtCore.Qt.WA_TranslucentBackground)
        
        self.LineEdit.returnPressed.connect(self.accept)
        
        self.show()
        
    def paintEvent(self, ev):
        # NOTE https://stackoverflow.com/questions/20802315/round-edges-corner-on-a-qwidget-in-pyqt
        painter = QtGui.QPainter(self)
        painter.begin(self)
        # NOTE 添加灰度过渡
        gradient = QtGui.QLinearGradient(QtCore.QRectF(self.rect()).topLeft(),QtCore.QRectF(self.rect()).bottomLeft())
        gradient.setColorAt(0.0, QtCore.Qt.black)
        gradient.setColorAt(0.4, QtCore.Qt.gray)
        gradient.setColorAt(0.7, QtCore.Qt.black)
        painter.setBrush(gradient)
        painter.drawRoundedRect(self.rect(), 10.0, 10.0)
        painter.end()
        
    def show(self):
        super(Launcher, self).show()
        self.LineEdit.setFocus()
        
    def accept(self):
        
        # NOTE 如果可以获取到 Game 路径 | 自动定位
        text = self.LineEdit.text()
        search = re.search(r"'(/Game/.*?)'",text)
        
        if not search:
            self.LineEdit.setStyleSheet("border-color:red")
            return
        
        path = search.group(1)
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            self.LineEdit.setStyleSheet("border-color:red")
            return
        
        unreal.EditorAssetLibrary.sync_browser_to_objects([path])
        self.hide()

def show():
    global launcher
    launcher = Launcher()
    # clear out, move and show
    launcher.LineEdit.setText("")
    position_window(launcher)

def position_window(window):
    """Position window to mouse cursor"""
    pos = QtGui.QCursor.pos()
    window.move(pos.x(), pos.y())

if __name__ == "__main__":
    show()

