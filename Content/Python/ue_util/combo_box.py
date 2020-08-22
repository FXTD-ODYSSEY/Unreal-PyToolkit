# -*- coding: utf-8 -*-
"""
可以输入带提示的 下拉菜单 组件
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-07-18 21:09:23'

from Qt import QtCore, QtWidgets, QtGui
from dayu_widgets.combo_box import MComboBox
from dayu_widgets.mixin import property_mixin, cursor_mixin, focus_shadow_mixin
# class TComboBox(QtWidgets.QComboBox):
from dayu_widgets import dayu_theme

@property_mixin
class MCompleter(QtWidgets.QCompleter):
    def __init__(self,parent=None):
        super(MCompleter, self).__init__(parent)
        dayu_theme.apply(self.popup())
        # popup.setStyleSheet(popup.styleSheet() + """
        # border: 0.5px solid black;
        # """)

class TComboBox(MComboBox):

    popup = QtCore.Signal()

    def __init__(self,  parent=None):
        super(TComboBox, self).__init__(parent)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)
        self.completer = MCompleter(self)

        # always show all completions
        self.completer.setCompletionMode(
            QtWidgets.QCompleter.UnfilteredPopupCompletion)
        self.pFilterModel = QtCore.QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(QtGui.QStandardItemModel())

        self.completer.setPopup(self.view())

        self.setCompleter(self.completer)

        edit = self.lineEdit()
        edit.setReadOnly(False)
        # NOTE 取消按 Enter 生成新 item 的功能
        edit.returnPressed.disconnect()
        edit.textEdited[unicode].connect(
            self.pFilterModel.setFilterFixedString)
        self.completer.activated.connect(self.setTextIfCompleterIsClicked)

    def clear(self):
        self.pFilterModel.setSourceModel(QtGui.QStandardItemModel())
        super(TComboBox, self).clear()

    def addItems(self, texts):
        # super(TComboBox,self).addItems(texts)
        for text in texts:
            self.addItem(text)

    def addItem(self, *args):
        super(TComboBox, self).addItem(*args)
        if len(args) == 2:
            _, text = args
        else:
            text = args[0]

        model = self.pFilterModel.sourceModel()

        item = QtGui.QStandardItem(text)
        model.setItem(model.rowCount(), item)

        if self.completer.model() != self.pFilterModel:
            self.completer.setModel(self.pFilterModel)

    def setModel(self, model):
        super(TComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(TComboBox, self).setModelColumn(column)

    def view(self):
        return self.completer.popup()

    def index(self):
        return self.currentIndex()

    def setTextIfCompleterIsClicked(self, text):
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)

    def showPopup(self):
        self.popup.emit()
        super(TComboBox, self).showPopup()

    def eventFilter(self, widget, event):
        return False