# -*- coding: utf-8 -*-
"""
场景放置工具
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2020-09-28 21:29:03"


import os
import tempfile
import posixpath
import webbrowser
from functools import partial
import unreal

from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import load_ui
from ue_util import error_log, toast, unreal_progress

level_lib = unreal.EditorLevelLibrary()
asset_lib = unreal.EditorAssetLibrary()
sys_lib = unreal.SystemLibrary()
py_lib = unreal.PyToolkitBPLibrary()

TRANSCATION = "placer"


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

        self.Label.setStyleSheet("font-size:10px")
        self.Label.setMinimumHeight(30)
        self.Label.setWordWrap(True)
        # font = self.Label.font()

        layout.addWidget(self.Image)
        layout.addWidget(self.Label)

        self.asset = asset
        asset_name = str(asset.get_name())
        if len(asset_name) >= 8:
            asset_name = "%s\n%s" % (asset_name[:8], asset_name[8:])
        self.Label.setText(asset_name)
        self.item_path = asset.get_full_name().split(" ")[-1]
        self.setToolTip(self.item_path)

        # NOTE 设置 menu 对象
        self.menu = QtWidgets.QMenu(self)
        locate_action = QtWidgets.QAction(u"定位资源", self)
        locate_action.triggered.connect(self.locate_item)

        open_action = QtWidgets.QAction(u"打开路径", self)
        open_action.triggered.connect(self.open_item)

        copy_action = QtWidgets.QAction(u"复制名称", self)
        copy_action.triggered.connect(self.open_item_name)

        remove_action = QtWidgets.QAction(u"删除资源", self)
        remove_action.triggered.connect(self.remove_items)

        self.menu.addAction(locate_action)
        self.menu.addAction(open_action)
        self.menu.addAction(copy_action)
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

    def open_item(self):
        if not self.check_item():
            return
        project = sys_lib.get_project_content_directory()
        path = self.item_path.replace("/Game/", project)
        path = os.path.dirname(path)
        if os.path.exists(path):
            os.startfile(path)
        else:
            toast(u"当前选择元素路径不存在")

    def open_item_name(self):
        if not self.check_item():
            return

        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(os.path.basename(self.item_path), mode=cb.Clipboard)

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
        location = (
            selected[-1].get_actor_location() if selected else unreal.Vector(0, 0, 0)
        )
        sys_lib.begin_transaction(TRANSCATION, "spawn actor", None)
        level_lib.spawn_actor_from_object(self.asset, location)
        sys_lib.end_transaction()


class PlacerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(PlacerWidget, self).__init__(parent)
        DIR, file_name = os.path.split(__file__)
        file_name = os.path.splitext(file_name)[0]
        load_ui(os.path.join(DIR, "%s.ui" % file_name), self)

        # NOTE 初始化 QSettings
        ini = posixpath.join(tempfile.gettempdir(), "%s.ini" % self.__class__.__name__)
        self.settings = QtCore.QSettings(ini, QtCore.QSettings.IniFormat)

        # NOTE 记录 Splitter 的位置
        self.Splitter.splitterMoved.connect(
            lambda: self.settings.setValue("splitter_size", self.Splitter.sizes())
        )
        splitter_size = self.settings.value("splitter_size")
        self.Splitter.setSizes(
            [int(i) for i in splitter_size] if splitter_size else [0, 1]
        )

        # self.get_content_path()
        self.Content_BTN.clicked.connect(self.get_content_path)

        self.Actor_Container.hide()
        self.Align_Pick_BTN.clicked.connect(lambda: self.get_selected_actors(True))

        self.Align_BTN.clicked.connect(self.align_selected)
        self.Filter_LE.textChanged.connect(self.filter_item)

        self.Transform_BTN.clicked.connect(self.offset_actor)
        self.MirrorActor_BTN.clicked.connect(self.mirror_axis)

        commands = [
            "SnapOriginToGrid",
            "SnapOriginToGridPerActor",
            "AlignOriginToGrid",
            "SnapToFloor",
            "SnapPivotToFloor",
            "SnapBottomCenterBoundsToFloor",
            "LockActorMovement",
            "SelectAll",
            "SelectNone",
            "InvertSelection",
            "SelectImmediateChildren",
            "SelectAllDescendants",
            "SelectRelevantLights",
            "SelectAllWithSameMaterial",
            "AttachSelectedActors",
            "AlignToActor",
            "AlignPivotToActor",
        ]
        for command in commands:
            button = getattr(self, "%s_BTN" % command)
            callback = partial(py_lib.exec_level_editor_action, command)
            button.clicked.connect(callback)

    def mirror_axis(self):
        x = self.MirrorActorX_RB.isChecked()
        y = self.MirrorActorY_RB.isChecked()
        z = self.MirrorActorZ_RB.isChecked()
        if x:
            py_lib.exec_level_editor_action("MirrorActorX")
        elif y:
            py_lib.exec_level_editor_action("MirrorActorY")
        elif z:
            py_lib.exec_level_editor_action("MirrorActorZ")

    def offset_actor(self):
        actors = level_lib.get_selected_level_actors()
        if not actors:
            return

        x = self.TransformX_SB.value()
        y = self.TransformY_SB.value()
        z = self.TransformZ_SB.value()
        sys_lib.begin_transaction(TRANSCATION, "offset actor", None)
        for actor in actors:
            actor.modify(True)
            actor.add_actor_local_offset(unreal.Vector(x, y, z), False, False)
            actor.modify(False)
        sys_lib.end_transaction()

    def filter_item(self, text):

        for i in range(self.List_Container.count()):
            item = self.List_Container.item(i)
            widget = self.List_Container.itemWidget(item)
            name = widget.Label.text()
            # NOTE 不区分大小写
            if not name.lower().startswith(text.lower()) and text:
                item.setHidden(True)
            else:
                item.setHidden(False)

    def get_selected_actors(self, click=False):
        actors = level_lib.get_selected_level_actors()
        if click:
            if not actors:
                toast(u"请选择一个物体")
                return
            actor = actors[0]
            self.Align_LE.setText(actor.get_path_name())
            return

        if len(actors) < 2:
            msg = u"请选择两个物体"
            toast(msg)
            raise RuntimeError(msg)

        return actors[-1], actors[:-1]

    def align_selected(self):

        align_actor = self.Align_LE.text()
        origin = unreal.load_object(None, align_actor)
        if origin:
            targets = level_lib.get_selected_level_actors()
        else:
            origin, targets = self.get_selected_actors()

        # NOTE 配置 undo
        # NOTE https://github.com/20tab/UnrealEnginePython/blob/master/docs/Transactions_API.md
        sys_lib.begin_transaction(TRANSCATION, "align selected", None)
        for target in targets:
            location = origin.get_actor_location()
            rotation = origin.get_actor_rotation()
            # NOTE 设置 undo
            target.modify(True)
            target.set_actor_location_and_rotation(location, rotation, False, False)
            # NOTE 选择 actors
            level_lib.set_selected_level_actors([target])
            target.modify(False)
        sys_lib.end_transaction()

    def get_content_path(self):

        directory = py_lib.get_current_content_path()
        self.Content_LE.setText(directory)

        self.List_Container.clear()
        size = 128
        assets = asset_lib.list_assets(directory)
        # NOTE 缩略图处理
        for i, asset_path in unreal_progress(assets):
            asset = unreal.load_asset(asset_path)
            if not isinstance(asset, unreal.StaticMesh):
                continue
            widget = PlacerItem(asset, self)
            data = "".join([chr(v) for v in py_lib.get_thumbnial(asset)])
            image = QtGui.QImage(data, size, size, QtGui.QImage.Format_RGB32)
            widget.setPixmap(QtGui.QPixmap.fromImage(image).scaled(size / 2, size / 2))
            item = QtWidgets.QListWidgetItem(self.List_Container)
            self.List_Container.addItem(item)
            item.setSizeHint(widget.sizeHint())
            self.List_Container.setItemWidget(item, widget)


@error_log
def main():
    Placer = PlacerWidget()
    Placer.show()


if __name__ == "__main__":
    main()
