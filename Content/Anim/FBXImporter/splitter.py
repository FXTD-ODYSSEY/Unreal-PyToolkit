# -*- coding: utf-8 -*-
"""
https://stackoverflow.com/questions/21997090/pyqt-qt4-how-to-add-a-tiny-arrow-collapse-button-to-qsplitter
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-05-31 15:53:13'


from Qt import QtCore, QtWidgets


class ISplitter(QtWidgets.QSplitter):
    def __init__(self, Orientation=QtCore.Qt.Horizontal, parent=None):
        super(ISplitter, self).__init__(Orientation, parent=parent)
        self.setHandleWidth(10)

    def handleSplitterButton(self, index,left=True):
        size_list = self.sizes()
        if not size_list[index-1]:
            size_list[index-1] = 1
        elif not size_list[index]:
            size_list[index] = 1
        else:
            size_list[index-1] = 0 if left else 1
            size_list[index] = 1 if left else 0
        self.setSizes(size_list)
        
    def createHandle(self):
        count = self.count()

        Orientation = self.orientation() 
        handle = QtWidgets.QSplitterHandle(Orientation,self)

        # NOTE 双击平均分配
        handle.mouseDoubleClickEvent = lambda event:self.setSizes([1 for i in range(self.count())])

        layout = QtWidgets.QVBoxLayout(
        ) if Orientation is QtCore.Qt.Horizontal else QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        handle.setLayout(layout)

        button = QtWidgets.QToolButton(handle)
        button.setArrowType(
            QtCore.Qt.LeftArrow if Orientation is QtCore.Qt.Horizontal else QtCore.Qt.UpArrow)
        button.clicked.connect(
            lambda: self.handleSplitterButton(count,True))
        layout.addWidget(button)
        button = QtWidgets.QToolButton(handle)
        button.setArrowType(
            QtCore.Qt.RightArrow if Orientation is QtCore.Qt.Horizontal else QtCore.Qt.DownArrow)
        button.clicked.connect(
            lambda: self.handleSplitterButton(count,False))
        layout.addWidget(button)
        
        return handle


if __name__ == '__main__':

    import sys
    app = QtWidgets.QApplication(sys.argv)

    splitter = ISplitter(QtCore.Qt.Vertical)
    splitter.addWidget(QtWidgets.QTextEdit())
    splitter.addWidget(QtWidgets.QTextEdit())
    splitter.addWidget(QtWidgets.QTextEdit())

    window = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout()
    window.setLayout(layout)
    layout.addWidget(splitter)

    window.show()
    
    sys.exit(app.exec_())
