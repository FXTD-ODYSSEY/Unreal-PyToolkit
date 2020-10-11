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
import tempfile
import posixpath
import webbrowser

import unreal

from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import load_ui, QFileDialog
from UE_Util import error_log, toast

level_lib = unreal.EditorLevelLibrary()
util_lib = unreal.EditorUtilityLibrary()
asset_lib = unreal.EditorAssetLibrary()
sys_lib = unreal.SystemLibrary()
py_lib = unreal.PyToolkitBPLibrary()


def unreal_progress(tasks):
    with unreal.ScopedSlowTask(len(tasks), u"读取资源") as task:
        task.make_dialog(True)
        for i, item in enumerate(tasks):
            if task.should_cancel():
                break
            task.enter_progress_frame(1, "进度 %s/%s" % (i, len(tasks)))
            yield i, item


class PlacerItem(QtWidgets.QWidget):
    def __init__(self, asset, parent=None):
        super(PlacerItem, self).__init__(parent)

        # self.placer_win = parent

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.Image = QtWidgets.QLabel()
        self.Image.setAlignment(QtCore.Qt.AlignCenter)
        self.Label = QtWidgets.QLabel()
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setWordWrap(True)
        self.Label.setScaledContents(True)

        layout.addWidget(self.Image)
        layout.addWidget(self.Label)

        self.asset = asset
        self.Label.setText(asset.get_name())
        self.item_path = asset.get_full_name().split(' ')[-1]
        self.setToolTip(self.item_path)

        # NOTE 设置 menu 对象
        self.menu = QtWidgets.QMenu(self)
        locate_action = QtWidgets.QAction(u'定位资源', self)
        locate_action.triggered.connect(self.locate_item)

        oepn_action = QtWidgets.QAction(u'打开路径', self)
        oepn_action.triggered.connect(self.oepn_item)

        remove_action = QtWidgets.QAction(u'删除资源', self)
        remove_action.triggered.connect(self.remove_items)

        self.menu.addAction(locate_action)
        self.menu.addAction(oepn_action)
        # self.menu.addAction(remove_action)

        # NOTE 设置右键菜单
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.popup_menu)

    def check_item(self):
        if not asset_lib.does_asset_exist(self.item_path):
            toast(u"资源路径不存在")
            return False
        return True

    def locate_item(self):
        if self.check_item():
            asset_lib.sync_browser_to_objects([self.item_path])

    def oepn_item(self):
        if not self.check_item():
            return
        project = sys_lib.get_project_content_directory()
        path = self.item_path.replace("/Game/", project)
        path = os.path.dirname(path)
        if os.path.exists(path):
            os.startfile(path)
        else:
            toast(u"当前选择元素路径不存在")

    def remove_items(self):
        pass

    def popup_menu(self):
        self.menu.popup(QtGui.QCursor.pos())

    def setPixmap(self, pixmap):
        return self.Image.setPixmap(pixmap)

    def mouseDoubleClickEvent(self, event):
        """
        双击生成 物体
        """
        super(PlacerItem, self).mouseDoubleClickEvent(event)
        
        selected = level_lib.get_selected_level_actors()
        location = selected[-1].get_actor_location(
        ) if selected else unreal.Vector(0, 0, 0)
        level_lib.spawn_actor_from_object(self.asset, location)


class PlacerWin(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(PlacerWin, self).__init__(parent)
        DIR, file_name = os.path.split(__file__)
        file_name = os.path.splitext(file_name)[0]
        load_ui(os.path.join(DIR, "%s.ui" % file_name), self)

        # NOTE 初始化 QSettings
        ini = posixpath.join(tempfile.gettempdir(), "%s.ini" %
                             self.__class__.__name__)
        self.settings = QtCore.QSettings(ini, QtCore.QSettings.IniFormat)

        # NOTE 记录 Splitter 的位置
        self.Splitter.splitterMoved.connect(
            lambda: self.settings.setValue("splitter_size", self.Splitter.sizes()))
        splitter_size = self.settings.value("splitter_size")
        # self.Splitter.setSizes(
        #     [int(i) for i in splitter_size] if splitter_size else [0, 1])
        self.Splitter.setSizes(
            [int(i) for i in splitter_size] if splitter_size else [0, 1])

        # self.get_content_path()
        self.Content_BTN.clicked.connect(self.get_content_path)

        self.Align_BTN.clicked.connect(self.align_selected)
        # self.L_Up_Align_BTN.clicked.connect(self.align_l_up)

    def get_selected_actors(self):
        actors = level_lib.get_selected_level_actors()
        if len(actors) < 2:
            msg = u"请选择两个场景物体"
            toast(msg)
            raise RuntimeError(msg)
        return actors[-2], actors[-1]

    def align_selected(self):
        origin, target = self.get_selected_actors()
        location = origin.get_actor_location()
        rotation = origin.get_actor_rotation()
        target.set_actor_location_and_rotation(
            location, rotation, False, False)
        # NOTE 选择 actors
        level_lib.set_selected_level_actors([target])

    def align_l_up(self):
        base, target = self.get_selected_actors()
        info = level_lib.get_level_viewport_camera_info()
        if not info:
            toast(u"无法获取摄像机信息")
            return
        cam_location, cam_rotation = info
        origin,extent = base.get_actor_bounds(True)
        
        line = cam_location - origin
        line.normalize()
        x_val = line.dot(unreal.Vector(1,0,0))
        y_val = line.dot(unreal.Vector(0,1,0))
        z_val = line.dot(unreal.Vector(0,0,1))

        # NOTE 正对 X 轴
        if x_val > 0.5:
            pass
        
        # level_lib = unreal.EditorLevelLibrary()
        # util_lib = unreal.EditorUtilityLibrary()
        # asset_lib = unreal.EditorAssetLibrary()
        # sys_lib = unreal.SystemLibrary()
        # py_lib = unreal.PyToolkitBPLibrary()

        # cam_location, cam_rotation = level_lib.get_level_viewport_camera_info()
        # base, target = level_lib.get_selected_level_actors()
        # origin,extent = base.get_actor_bounds(True)
        # line = cam_location - origin
        # line.normalize()
        # x_val = line.dot(unreal.Vector(1,0,0))
        # y_val = line.dot(unreal.Vector(0,1,0))
        # z_val = line.dot(unreal.Vector(0,0,1))
        # print(cam_rotation)
        # print(x_val)
        # print(y_val)
        # print(z_val)


        
    def get_content_path(self):

        directory = py_lib.get_current_content_path()
        self.Content_LE.setText(directory)

        self.List_Container.clear()
        size = 128
        assets = asset_lib.list_assets(directory)
        for i, asset_path in unreal_progress(assets):
            asset = unreal.load_asset(asset_path)
            if not isinstance(asset, unreal.StaticMesh):
                continue
            widget = PlacerItem(asset, self)
            data = "".join([chr(v) for v in py_lib.get_thumbnial(asset)])
            image = QtGui.QImage(data, size, size, QtGui.QImage.Format_RGB32)
            widget.setPixmap(QtGui.QPixmap.fromImage(
                image).scaled(size/2, size/2))
            item = QtWidgets.QListWidgetItem(self.List_Container)
            self.List_Container.addItem(item)
            item.setSizeHint(widget.sizeHint())
            self.List_Container.setItemWidget(item, widget)

    def get_camera_info(self):
        """获取 Camera 位置信息"""
        return level_lib.get_level_viewport_camera_info()


@error_log
def main():
    Placer = PlacerWin()
    Placer.show()


if __name__ == "__main__":
    main()
    
