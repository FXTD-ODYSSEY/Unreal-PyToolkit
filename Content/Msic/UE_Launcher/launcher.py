# -*- coding: utf-8 -*-
"""
UE 启动器
- [x] 资源路径定位
- [ ] 资源搜索 | 当前文件夹内搜索
- [ ] 配合 shift 键 打开资源
- [ ] Actor 搜索
- [ ] 菜单栏搜索
- [ ] Python API 搜索
- [ ] C++ API 搜索
- [ ] 搜索引擎 bing gg bd
- [ ] 支持下来菜单配置 置顶 | 收藏夹
- [ ] Cmd 命令触发
- [ ] ~python 多行模式支持 | 代码高亮~
- [ ] ~Unreal 内置命令整合 (保存资源之类)~

- [ ] 学习参考 Maya cosmos 插件

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

def error_display(func):
    def wrapper(self,*args, **kwargs):
        try:
            res = func(self,*args, **kwargs)
            return res
        except Exception as e:
            self.Error_Label.setVisible(True)
            self.Error_Label.setText(u"%s" % e)
            self.Error_Label.setStyleSheet('color: red;background-color:transparent')
            self.LineEdit.setStyleSheet("border-color:red")
    return wrapper
    

asset_lib = unreal.EditorAssetLibrary
py_lib = unreal.PyToolkitBPLibrary
class Launcher(QtWidgets.QWidget):

    """A menu to find and execute Maya commands and user scripts."""
        
    def __init__(self, *args, **kwds):
        super(Launcher, self).__init__(*args, **kwds)

        DIR,file_name = os.path.split(__file__)
        base_name,_ = os.path.splitext(file_name)
        ui_path = os.path.join(DIR,"%s.ui" % base_name)
        QtCompat.loadUi(ui_path,self)

        # NOTE 隐藏 Error_Label
        self.Error_Label.hide()
        
        # NOTE 设置图标
        style = QtWidgets.QApplication.style()
        icon = style.standardIcon(QtWidgets.QStyle.SP_FileDialogContentsView)
        pixmap = icon.pixmap(32,32)
        # pixmap = style.standardPixmap(QtWidgets.QStyle.SP_FileDialogContentsView)
        bitmap = pixmap.createMaskFromColor(QtGui.QColor(50, 50, 50))
        pixmap.setMask(bitmap)
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
        
    def check_path(self,path):
        if not path:
            return
        
        # NOTE 如果路径带了前后引号
        if ((path.startswith('"') and path.endswith('"'))
                or (path.startswith("'") and path.endswith("'"))):
            path = path[1:-1]
            
        path = path.replace('\\','/')
        project = unreal.SystemLibrary.get_project_content_directory()
        if path.startswith(project):
            path = path.replace(project,"/Game/")
            
            
        search = re.search(r"(/Game/.*?)",path)
        
        path,_ = os.path.splitext(path)
        if not search:
            return
        return path
    
    def show(self):
        # NOTE 获取粘贴板的文本
        cb = QtWidgets.QApplication.clipboard()
        text = cb.text()
        path = self.check_path(text)
        if path:
            self.LineEdit.setText(text)
            self.LineEdit.selectAll()
            
        self.LineEdit.setFocus()
        super(Launcher, self).show()
    
    @error_display
    def accept(self):
        
        # NOTE 如果可以获取到 Game 路径 | 自动定位
        text = self.LineEdit.text()
        path = self.check_path(text)
        # print("path",path)
        if not path:
            raise RuntimeError(u"不是正确的路径")
        
        if asset_lib.does_asset_exist(path):
            asset = unreal.load_asset(path)
            if isinstance(asset,unreal.World):
                py_lib.set_selected_folders([os.path.dirname(path)])
            else:
                asset_lib.sync_browser_to_objects([path])
        elif asset_lib.does_directory_exist(path):
            py_lib.set_selected_folders([path])
        else:
            raise RuntimeError(u"路径文件不存在")
        
        self.hide()

def position_window(window):
    """Position window to mouse cursor"""
    pos = QtGui.QCursor.pos()
    window.move(pos.x(), pos.y())

def show():
    global launcher
    launcher = Launcher()
    # clear out, move and show
    position_window(launcher)
    
    
if __name__ == "__main__":
    show()

