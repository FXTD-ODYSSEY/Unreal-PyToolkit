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

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2020-07-30 20:11:42"


import os
import re
import sys
import inspect
import threading
from collections import defaultdict

import unreal

from ue_util import unreal_progress
from QBinder import BinderTemplate
from Qt import QtCore, QtGui, QtWidgets, QtCompat


asset_lib = unreal.EditorAssetLibrary
py_lib = unreal.PyToolkitBPLibrary
asset_reg = unreal.AssetRegistryHelpers.get_asset_registry()


class ThreadBase(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(ThreadBase, self).__init__(*args, **kwargs)
        self.callbacks = []

    def bind(self, callback):
        self.callbacks.append(callback)

    def unbind(self, callback):
        self.callbacks.remove(callback)


class LauncherBinder(BinderTemplate):
    def __init__(self):
        self.loading_vis = False


class LauncherBase(QtWidgets.QWidget):

    """A menu to find and execute Maya commands and user scripts."""

    state = LauncherBinder()
    __instance = None

    @classmethod
    def instance(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = cls(*args, **kwargs)
        return cls.__instance

    @classmethod
    def popup(cls):
        """Position window to mouse cursor"""
        launcher = cls.instance()
        launcher.move(QtGui.QCursor.pos())
        launcher.show()

    def __init__(self, *args, **kwargs):
        super(LauncherBase, self).__init__(*args, **kwargs)

        DIR, file_name = os.path.split(__file__)
        base_name, _ = os.path.splitext(file_name)
        ui_path = os.path.join(DIR, "%s.ui" % base_name)
        QtCompat.loadUi(ui_path, self)

        self.offset = QtCore.QPoint()

        self.Search_List.hide()
        self.Search_Combo.hide()
        self.Search_Label.hide()
        self.Loading_Container.setVisible(lambda: self.state.loading_vis * 1)

        # NOTE 设置图标
        style = QtWidgets.QApplication.style()
        icon = style.standardIcon(QtWidgets.QStyle.SP_FileDialogContentsView)
        self.Settings_BTN.setIcon(icon)
        icon = style.standardIcon(QtWidgets.QStyle.SP_BrowserReload)
        self.loading_pixmap = icon.pixmap(20, 20)
        self.Loading_Icon.setPixmap(self.loading_pixmap)
        self.Loading_Icon.setFixedSize(25, 25)

        self.Settings_BTN.setMenu(self.Settings_Menu)
        self.Settings_BTN.clicked.connect(self.Settings_BTN.showMenu)

        # NOTE loading 按钮旋转动画
        self.loading_animation = QtCore.QVariantAnimation(
            self,
            startValue=0.0,
            endValue=360.0,
            duration=1000,
        )
        self.loading_animation.valueChanged.connect(
            lambda value: self.Loading_Icon.setPixmap(
                self.loading_pixmap.transformed(QtGui.QTransform().rotate(value))
            )
        )
        self.loading_animation.finished.connect(self.loading_animation.start)
        self.loading_animation.start()

        # TODO 设置状态标签

        self.setWindowFlags(QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.Search_LE.search()
        self.Search_LE.setPlaceholderText("")
        self.Search_LE.returnPressed.connect(self.accept)
        self.adjustSize()

    def mousePressEvent(self, event):
        self.offset = event.pos()
        super(LauncherBase, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        x = event.globalX()
        y = event.globalY()
        x_w = self.offset.x()
        y_w = self.offset.y()
        self.move(x - x_w, y - y_w)
        super(LauncherBase, self).mouseMoveEvent(event)

    def paintEvent(self, event):

        # NOTE https://stackoverflow.com/questions/20802315/round-edges-corner-on-a-qwidget-in-pyqt
        painter = QtGui.QPainter(self)
        painter.setRenderHint(painter.Antialiasing)
        painter.begin(self)
        # NOTE 添加灰度过渡
        gradient = QtGui.QLinearGradient(
            QtCore.QRectF(self.rect()).topLeft(),
            QtCore.QRectF(self.rect()).bottomLeft(),
        )
        gradient.setColorAt(0.2, QtGui.QColor(34, 34, 34))
        gradient.setColorAt(0.5, QtGui.QColor(111, 111, 111))
        gradient.setColorAt(0.8, QtGui.QColor(34, 34, 34))
        painter.setBrush(gradient)
        painter.drawRoundedRect(self.rect(), 10.0, 10.0)

        path = QtGui.QPainterPath()
        pen = QtGui.QPen(QtGui.QColor(34, 34, 34), 5)
        painter.setPen(pen)
        path.addRoundedRect(self.rect(), 10, 10)
        painter.setClipPath(path)
        painter.strokePath(path, painter.pen())
        painter.end()

        super(LauncherBase, self).paintEvent(event)

    def show(self):
        # NOTE 获取粘贴板的文本
        cb = QtWidgets.QApplication.clipboard()
        text = cb.text()
        path = self.check_path(text)
        if path:
            self.Search_LE.setText(text)
            self.Search_LE.selectAll()

        self.Search_LE.setFocus()
        super(LauncherBase, self).show()


class CollectUnrealDirThread(ThreadBase):
    def run(self):
        """
        Get Unreal Class Member link to python documentation
        """
        link_list = []
        method_dict = defaultdict(list)
        for cls_name, cls in inspect.getmembers(unreal, inspect.isclass):
            p_methods = [
                n for n, m in inspect.getmembers(cls.__base__, inspect.isroutine)
            ]
            for m_name, method in inspect.getmembers(cls, inspect.isroutine):
                if m_name in p_methods or (
                    m_name.startswith("__") and m_name.endswith("__")
                ):
                    continue
                method_dict[cls].append(m_name)
                link_list.append(
                    "https://docs.unrealengine.com/en-US/PythonAPI/class/{cls}.html#unreal.{cls}.{method}".format(
                        cls=cls_name, method=m_name
                    )
                )
        for callback in self.callbacks:
            callback(link_list)


class Launcher(LauncherBase):
    def __init__(self, *args, **kwargs):
        super(Launcher, self).__init__(*args, **kwargs)

        self.completer = QtWidgets.QCompleter()
        self.model = QtCore.QStringListModel()
        self.completer.setModel(self.model)
        self.completer.setFilterMode(QtCore.Qt.MatchContains)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.Search_LE.setCompleter(self.completer)
        
        # # TODO 多进程加载 引擎 路径
        # self.asset_thread = CollectAssetThread()
        # self.asset_thread.bind(self.handle_asset)
        # self.asset_thread.start()

        # TODO 多线程加载 Python 链接
        self.cls_thread = CollectUnrealDirThread()
        self.cls_thread.bind(self.order_class)
        self.cls_thread.start()

        self.state.loading_vis = True
        self.get_asset_paths()

    def order_class(self, links):
        self.model.setStringList(self.model.stringList() + links)
        self.state.loading_vis = False

    def get_asset_paths(self):
        assets = asset_reg.get_all_assets()
        paths = [
            str(data.object_path)
            for _,data in unreal_progress(assets)
            if data.is_valid()
            and not data.is_redirector()
            and str(data.object_path).startswith("/Game/")
        ]

        self.model.setStringList(self.model.stringList() + paths)

    def check_path(self, path):
        if not path:
            return

        # NOTE 如果路径带了前后引号
        if (path.startswith('"') and path.endswith('"')) or (
            path.startswith("'") and path.endswith("'")
        ):
            path = path[1:-1]

        path = path.replace("\\", "/")
        project = unreal.SystemLibrary.get_project_content_directory()
        if path.startswith(project):
            path = path.replace(project, "/Game/")

        search = re.search(r"(/Game/.*?)", path)

        path, _ = os.path.splitext(path)
        if not search:
            return
        return path

    def accept(self):

        # NOTE 如果可以获取到 Game 路径 | 自动定位
        text = self.Search_LE.text()
        path = self.check_path(text)
        # print("path",path)
        if not path:
            raise RuntimeError(u"不是正确的路径")

        if asset_lib.does_asset_exist(path):
            asset = unreal.load_asset(path)
            if isinstance(asset, unreal.World):
                py_lib.set_selected_folders([os.path.dirname(path)])
            else:
                asset_lib.sync_browser_to_objects([path])
        elif asset_lib.does_directory_exist(path):
            py_lib.set_selected_folders([path])
        else:
            raise RuntimeError(u"路径文件不存在")

        self.hide()


if __name__ == "__main__":
    Launcher.popup()
