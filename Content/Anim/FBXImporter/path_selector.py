# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-05-31 08:01:14'

from Qt import QtGui
from Qt import QtCore
from Qt import QtWidgets

from functools import partial
from dayu_widgets.line_edit import MLineEdit
from dayu_widgets.push_button import MPushButton

class IPathSelector(QtWidgets.QWidget):
    def __init__(self, parent=None, select_callback=None, label=u"文件路径", button_text=u"浏览"):
        super(IPathSelector, self).__init__(parent=parent)

        self.label = QtWidgets.QLabel(label)

        self.line = MLineEdit()

        self.button = MPushButton()
        self.button.setText(button_text)
        callback = select_callback if callable(
            select_callback) else self.browser_file
        self.button.clicked.connect(partial(callback, self.line))

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(self.label)
        layout.addWidget(self.line)
        layout.addWidget(self.button)

    def browser_file(self, line):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Browser Folder')

        line.setText(path) if path else None


def test():
    app = QtWidgets.QApplication([])
    widget = IPathSelector()
    widget.show()
    app.exec_()


if __name__ == "__main__":
    test()
