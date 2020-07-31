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

        self.setWindowFlags(QtCore.Qt.Popup)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        # self.setFlags(QtCore.Qt.WA_TranslucentBackground)
        
        self.LineEdit.returnPressed.connect(self.accept)
        
        self.show()
        
        # app = QtWidgets.QApplication.instance()
        # app.installEventFilter(self)
    # def eventFilter(self, receiver, event):
    #     print("receiver",receiver,event,event.type())
    #     if not hasattr(event, "type"):
    #         return False
    #     # NOTE 键盘事件
    #     if event.type() == QtCore.QEvent.KeyRelease:
    #         print("key",event.key())
    #         # NOTE 敲击 Tab 键
    #         if event.key() == QtCore.Qt.Key_Tab and not self.isVisible():
    #             self.show()
    #     return False

    def paintEvent(self, ev):
        painter = QtGui.QPainter(self)
        painter.begin(self)
        # gradient = QtGui.QLinearGradient(QtCore.QRectF(self.rect()).topLeft(),QtCore.QRectF(self.rect()).bottomLeft())
        # gradient.setColorAt(0.0, QtCore.Qt.black)
        # gradient.setColorAt(0.4, QtCore.Qt.gray)
        # gradient.setColorAt(0.7, QtCore.Qt.black)
        # painter.setBrush(gradient)
        painter.drawRoundedRect(self.rect(), 10.0, 10.0)
        painter.end()
        
    def show(self):
        super(Launcher, self).show()
        self.LineEdit.setFocus()
        style = self.styleSheet()
        style += """
        #Launcher_Container{
            background:transparent;
        }
        """
        self.setStyleSheet(style)
        
    def accept(self):
        text = self.LineEdit.text()
        search = re.search(r"'(/Game/.*?)'",text)
        
        if not search:
            self.LineEdit.setStyleSheet("border-color:red")
            return
        
        path = search.group(1)
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

