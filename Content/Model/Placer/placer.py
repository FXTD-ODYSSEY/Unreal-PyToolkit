# -*- coding: utf-8 -*-
"""
场景放置工具
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-09-28 21:29:03'


import os
import re
import sys
import json
import webbrowser

import unreal

from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import load_ui, QFileDialog

editor_lib = unreal.EditorLevelLibrary()
level_lib = unreal.EditorLevelLibrary()

# class FlowLayout(QtGui.QLayout):
#     def __init__(self, parent=None, margin=0, spacing=-1):
#         super(FlowLayout, self).__init__(parent)

#         if parent is not None:
#             self.setContentsMargins(margin, margin, margin, margin)

#         self.setSpacing(spacing)
#         self.margin = margin
        
#         # spaces between each item
#         self.spaceX = 5
#         self.spaceY = 5

#         self.itemList = []

#     def __del__(self):
#         item = self.takeAt(0)
#         while item:
#             item = self.takeAt(0)

#     def addItem(self, item):
#         self.itemList.append(item)

#     def count(self):
#         return len(self.itemList)

#     def itemAt(self, index):
#         if index >= 0 and index < len(self.itemList):
#             return self.itemList[index]

#         return None

#     def takeAt(self, index):
#         if index >= 0 and index < len(self.itemList):
#             return self.itemList.pop(index)

#         return None

#     def expandingDirections(self):
#         return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

#     def hasHeightForWidth(self):
#         return True

#     def heightForWidth(self, width):
#         height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)
#         return height

#     def setGeometry(self, rect):
#         super(FlowLayout, self).setGeometry(rect)
#         self.doLayout(rect, False)

#     def sizeHint(self):
#         return self.minimumSize()

#     def minimumSize(self):
#         size = QtCore.QSize()

#         for item in self.itemList:
#             size = size.expandedTo(item.minimumSize())

#         size += QtCore.QSize(2 * self.margin, 2 * self.margin)
#         return size

#     def doLayout(self, rect, testOnly):
#         x = rect.x()
#         y = rect.y()
#         lineHeight = 0

#         for item in self.itemList:
#             wid = item.widget()
#             # spaceX = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Horizontal)
#             # spaceY = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Vertical)
#             nextX = x + item.sizeHint().width() + self.spaceX
#             if nextX - self.spaceX > rect.right() and lineHeight > 0:
#                 x = rect.x()
#                 y = y + lineHeight + self.spaceY
#                 nextX = x + item.sizeHint().width() + self.spaceX
#                 lineHeight = 0

#             if not testOnly:
#                 item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

#             x = nextX
#             lineHeight = max(lineHeight, item.sizeHint().height())

#         return y + lineHeight - rect.y()

class PlacerWin(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(PlacerWin, self).__init__(parent)
        DIR, file_name = os.path.split(__file__)
        file_name = os.path.splitext(file_name)[0]
        load_ui(os.path.join(DIR, "%s.ui" % file_name), self)
        
        
        
        
    def get_camera_info(self):
        """获取 Camera 位置信息"""
        return editor_lib.get_level_viewport_camera_info()
    
    def get_bounds(self):
        # NOTE 获取 选择的 bounding 信息

        origin,extent,radius = unreal.EditorUtilityLibrary.get_selection_bounds()
        print(extent)


