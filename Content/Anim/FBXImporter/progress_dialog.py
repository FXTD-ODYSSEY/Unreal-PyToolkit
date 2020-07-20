# coding:utf-8

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-03-09 17:13:54'

"""
进度条组件
"""

from Qt import QtGui
from Qt import QtWidgets
from Qt import QtCore


class IProgressDialog(QtWidgets.QProgressDialog):
    def __init__(self, status=u"进度", button_text=u"取消", minimum=0, maximum=100, parent=None, title=""):
        # super(IProgressDialog, self).__init__()
        QtWidgets.QProgressDialog.__init__(self,parent=parent)
        # self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowTitle(status if title else title)
        self.setLabelText(status)
        self.setCancelButtonText(button_text)
        self.setRange(minimum, maximum)
        self.setValue(minimum)
        self.show()
        # self.delay()

    def delay(self):
        u'''
        delay 延时1ms 防止gui无响应
        延时1ms操作 确保窗口不会呈空白
        '''
        loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(1, loop.quit)
        loop.exec_()

    def setLabelText(self, text):
        u'''
        setLabelText 设置加载文本

        该功能继承自 QProgressDialog 的 setLabelText
        加入延时功能来响应GUI
        Arguments:
            text {str} -- 加载文本
        '''
        QtWidgets.QProgressDialog.setLabelText(self,text)
        # super(IProgressDialog, self).setLabelText(text)
        self.delay()

    @classmethod
    def loop(cls, seq, **kwargs):

        self = cls(**kwargs)
        self.setMaximum(len(seq))
        for i, item in enumerate(seq, 1):
            if self.wasCanceled():
                break
            try:
                yield item  # with body executes here
            except:
                import traceback
                traceback.print_exc()
                self.deleteLater()
            self.setValue(i)
        self.deleteLater()


def test():
    app = QtWidgets.QApplication([])
    button = QtWidgets.QPushButton("click to popup the ProgressWindow")
    button.clicked.connect(
        lambda: [i for i in IProgressDialog.loop(range(999000), parent=button)])
    button.show()
    app.exec_()


if __name__ == "__main__":
    test()
