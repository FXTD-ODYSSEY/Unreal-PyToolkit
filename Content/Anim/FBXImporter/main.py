# -*- coding: utf-8 -*-
"""
检测导入的 FBX 和现有的动画资源的帧数
右键导入可以导入匹配对的动画资源
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-05-30 21:27:26'

import os
import sys
DIR = os.path.dirname(__file__)
sys.path.insert(0, DIR) if DIR else None

from dayu_widgets.push_button import MPushButton
from progress_dialog import IProgressDialog
from splitter import ISplitter
from path_selector import IPathSelector
from Qt import QtCore, QtWidgets, QtGui
from functools import partial
from collections import Iterable
from itertools import chain
import webbrowser
import unreal
import FbxCommon
import fbx



class ListSyncer(object):
    """
    用来同步两个 ListWidget 滚动和选择
    """
    protected = False

    def protected_decorator(func):
        def wrapper(self, *args, **kwargs):
            # NOTE 避免重复调用
            if self.protected:
                return
            self.protected = True
            func(self, *args, **kwargs)
            self.protected = False
        return wrapper

    def __init__(self, *args, **kwargs):
        # NOTE args 传入 ListWidget 列表，可以是层层嵌套的数据，下面的操作会自动过滤出 ListWidget 列表
        # NOTE flattern list https://stackoverflow.com/questions/17338913/flatten-list-of-list-through-list-comprehension
        widget_list = list(chain.from_iterable(item if isinstance(item, Iterable) and
                                               not isinstance(item, basestring) else [item] for item in args))

        self.widget_list = [widget for widget in widget_list if isinstance(
            widget, QtWidgets.QListWidget)]

        # NOTE 默认同步滚动
        if kwargs.get("scroll", True):
            self.scroll_list = [widget.verticalScrollBar()
                                for widget in self.widget_list]
            for scroll in self.scroll_list:
                # NOTE 默认 scroll_sync 参数不启用 | 滚动根据滚动值进行同步 | 反之则根据滚动百分比同步
                callback = partial(self.move_scrollbar, scroll) if kwargs.get(
                    "scroll_sync", False) else lambda value: [scroll.setValue(value) for scroll in self.scroll_list]
                scroll.valueChanged.connect(callback)

        # NOTE 同步选择 默认不同步
        if kwargs.get("selection", False):
            for widget in self.widget_list:
                callback = partial(self.item_selection, widget)
                widget.itemSelectionChanged.connect(callback)

    @protected_decorator
    def move_scrollbar(self, scroll, value):
        scroll.setValue(value)
        ratio = float(value)/scroll.maximum()
        for _scroll in self.scroll_list:
            # NOTE 跳过自己
            if scroll is _scroll:
                continue
            val = int(ratio*_scroll.maximum())
            _scroll.setValue(val)

    @protected_decorator
    def item_selection(self, widget):
        items = widget.selectedItems()
        row_list = [widget.row(item) for item in items]
        for _widget in self.widget_list:
            # NOTE 跳过自己
            if widget is _widget:
                continue
            _widget.clearSelection()
            for row in row_list:
                item = _widget.item(row)
                # NOTE 如果 item 存在选择 item
                if item:
                    item.setSelected(True)


class FBXListWidget(QtWidgets.QListWidget):

    def __init__(self, parent=None, file_filter=None):
        super(FBXListWidget, self).__init__()
        self.FBX_UI = parent
        self.asset_list = parent.asset_list
        self.file_filter = file_filter

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.customContextMenuRequested.connect(self.right_menu)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        event.accept() if event.mimeData().hasUrls() else event.ignore()

    def dropEvent(self, event):
        # Note 获取拖拽文件的地址
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            for url in IProgressDialog.loop(event.mimeData().urls()):
                path = (url.toLocalFile())
                _, ext = os.path.splitext(path)
                # Note 过滤已有的路径
                if ext.lower() in self.file_filter or "*" in self.file_filter:
                    self.addItem(path)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def right_menu(self):
        self.menu = QtWidgets.QMenu(self)

        open_file_action = QtWidgets.QAction(u'打开文件路径', self)
        open_file_action.triggered.connect(self.open_file_location)

        remove_action = QtWidgets.QAction(u'删除选择', self)
        remove_action.triggered.connect(self.remove_items)

        import_action = QtWidgets.QAction(u'导入选择', self)
        import_action.triggered.connect(self.import_items)

        item = self.currentItem()
        path = item.toolTip()
        path = path.split('\n')[0]
        if not os.path.exists(path):
            open_file_action.setVisible(False)

        self.menu.addAction(open_file_action)
        self.menu.addSeparator()
        self.menu.addAction(remove_action)
        self.menu.addSeparator()
        self.menu.addAction(import_action)
        self.menu.popup(QtGui.QCursor.pos())

    def open_file_location(self):
        item = self.currentItem()
        path = item.toolTip()
        path = path.split('\n')[0]
        print(path)
        os.startfile(os.path.dirname(path))

    def remove_items(self):
        style = QtWidgets.QApplication.style()
        icon = style.standardIcon(QtWidgets.QStyle.SP_MessageBoxQuestion)
        # NOTE 如果没有选择 直接删除当前项
        for item in self.selectedItems():
            row = self.row(item)
            count = self.asset_list.count()
            if row < count:
                item.setText("")
                item.setToolTip("")
                item.setIcon(icon)
            else:
                item = self.takeItem(row)

    def buildImportTask(self, filename='', destination_path='', skeleton=None):

        options = unreal.FbxImportUI()
        options.set_editor_property("skeleton", skeleton)
        # NOTE 只导入 动画 数据
        options.set_editor_property("import_animations", True)
        options.set_editor_property("import_as_skeletal", False)
        options.set_editor_property("import_materials", False)
        options.set_editor_property("import_textures", False)
        options.set_editor_property("import_rigid_mesh", False)
        options.set_editor_property("create_physics_asset", False)
        options.set_editor_property(
            "mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
        # NOTE https://forums.unrealengine.com/development-discussion/python-scripting/1576474-importing-skeletal-meshes-4-21
        options.set_editor_property(
            "automated_import_should_detect_type", False)

        task = unreal.AssetImportTask()
        task.set_editor_property("factory", unreal.FbxFactory())
        # NOTE 设置 automated 为 True  不会弹窗
        task.set_editor_property("automated", True)
        task.set_editor_property("destination_name", '')
        task.set_editor_property("destination_path", destination_path)
        task.set_editor_property("filename", filename)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", False)
        task.options = options

        return task

    def import_items(self):
        # Note unreal 导入 FBX
        tasks = []
        for fbx_item in self.selectedItems():
            fbx_path = fbx_item.toolTip()
            if not fbx_path:
                continue
            fbx_path = fbx_path.split("\n")[0]
            row = self.row(fbx_item)
            asset_item = self.asset_list.item(row)
            asset_path = os.path.dirname(asset_item.text())
            skeleton = asset_item.asset.get_editor_property('skeleton')

            task = self.buildImportTask(fbx_path, asset_path, skeleton)
            tasks.append(task)

            # NOTE 配置颜色
            fbx_item.setBackground(QtGui.QBrush(QtGui.QColor(0, 255, 0)))
            asset_item.setBackground(QtGui.QBrush(QtGui.QColor(0, 255, 0)))

        # NOTE 批量导入 FBX
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    def read_fbx_frame(self, fbx_file):
        # NOTE read FBX frame count
        manager, scene = FbxCommon.InitializeSdkObjects()
        # NOTE 只导入 Global_Settings 读取帧数
        s = manager.GetIOSettings()
        s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Material", False)
        s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Texture", False)
        s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Audio", False)
        s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Audio", False)
        s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Shape", False)
        s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Link", False)
        s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Gobo", False)
        s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Animation", False)
        s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Character", False)
        s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Global_Settings", True)
        manager.SetIOSettings(s)

        result = FbxCommon.LoadScene(manager, scene, fbx_file)
        if not result:
            raise RuntimeError("%s load Fail" % fbx_file)

        # NOTE 获取 FBX 设定设置的帧数
        setting = scene.GetGlobalSettings()
        time_span = setting.GetTimelineDefaultTimeSpan()
        time_mode = setting.GetTimeMode()
        frame_rate = fbx.FbxTime.GetFrameRate(time_mode)
        duration = time_span.GetDuration()
        second = duration.GetMilliSeconds()
        frame_count = round(second/1000*frame_rate) + 1
        return frame_count

    def handleItem(self, item, callback):
        path = item.text() if isinstance(item, QtWidgets.QListWidgetItem) else item
        style = QtWidgets.QApplication.style()
        warn_icon = style.standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning)
        question_icon = style.standardIcon(
            QtWidgets.QStyle.SP_MessageBoxQuestion)
        file_name = ""
        if os.path.exists(path):
            file_name = os.path.basename(path)
            item = QtWidgets.QListWidgetItem(warn_icon, file_name)
            if self.findItems(file_name, QtCore.Qt.MatchContains):
                return
            item.frame_count = self.read_fbx_frame(path)
            tooltip = u"%s\n关键帧数: %s" % (path, item.frame_count)
            item.setToolTip(tooltip)
        elif path == "":
            item = QtWidgets.QListWidgetItem(question_icon, "")
        else:
            return

        callback(item)
        self.FBX_UI.compare_assets() if path else None

    def addItem(self, item):
        self.handleItem(item, lambda item: super(
            FBXListWidget, self).addItem(item))

    def addItems(self, items):
        for item in IProgressDialog.loop(items):
            self.addItem(item)

    def insertItem(self, row, item):
        self.handleItem(item, lambda item: super(
            FBXListWidget, self).insertItem(row, item))

    def insertItems(self, row, items):
        for item in IProgressDialog.loop(items):
            self.insertItem(row, item)


class AssetListWidget(QtWidgets.QListWidget):

    def __init__(self, parent=None):
        super(AssetListWidget, self).__init__(parent=parent)
        self.FBX_UI = parent
        self.setIconSize(QtCore.QSize(15, 15))
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_menu)

    def right_menu(self):
        self.menu = QtWidgets.QMenu(self)
        # NOTE 右键选择资源
        select_asset = QtWidgets.QAction(u'选择资源', self)
        select_asset.triggered.connect(self.sync_asset)
        select_assets = QtWidgets.QAction(u'选择已选中的资源', self)
        select_assets.triggered.connect(self.sync_assets)

        self.menu.addAction(select_asset)
        self.menu.addAction(select_assets)
        self.menu.popup(QtGui.QCursor.pos())

    def sync_asset(self):
        item = self.currentItem()
        path = item.text()
        unreal.EditorAssetLibrary.sync_browser_to_objects([path])

    def sync_assets(self):
        path_list = [item.text() for item in self.selectedItems()]
        unreal.EditorAssetLibrary.sync_browser_to_objects(path_list)


class FBXImporter_UI(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(FBXImporter_UI, self).__init__(*args, **kwargs)
        self.settings = QtCore.QSettings(
            self.__class__.__name__, QtCore.QSettings.IniFormat)

        self.setWindowTitle(u"FBX 动画导入比对面板")

        self.Unreal_Layout = QtWidgets.QVBoxLayout()
        self.Unreal_Layout.setContentsMargins(0, 0, 0, 0)
        self.selector = IPathSelector(
            select_callback=self.select_folder, button_text=u"获取选择资源的目录路径")

        self.asset_list = AssetListWidget(self)

        self.Unreal_Layout.addWidget(self.selector)
        self.Unreal_Layout.addWidget(self.asset_list)
        self.Unreal_Widget = QtWidgets.QWidget()
        self.Unreal_Widget.setLayout(self.Unreal_Layout)

        self.fbx_list = FBXListWidget(self, file_filter=[".fbx"])

        fbx_layout = QtWidgets.QVBoxLayout()
        fbx_layout.setContentsMargins(0, 0, 0, 0)
        butotn_layout = QtWidgets.QHBoxLayout()
        self.root_btn = MPushButton(u"获取文件目录路径")
        self.root_btn.clicked.connect(self.handle_directory)
        self.file_btn = MPushButton(u"获取文件")
        self.file_btn.clicked.connect(self.get_file)
        butotn_layout.addWidget(self.root_btn)
        butotn_layout.addWidget(self.file_btn)
        fbx_layout.addLayout(butotn_layout)
        fbx_layout.addWidget(self.fbx_list)
        fbx_widget = QtWidgets.QWidget()
        fbx_widget.setLayout(fbx_layout)

        # NOTE 同步滚动
        self.syncer = ListSyncer(
            self.asset_list, self.fbx_list, selection=True)

        self.compare_splitter = ISplitter()
        self.compare_splitter.addWidget(self.Unreal_Widget)
        self.compare_splitter.addWidget(fbx_widget)

        self.import_button = MPushButton(u"刷新")
        self.import_button.clicked.connect(self.refresh)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(9, 0, 9, 9)
        self.setLayout(layout)

        self.Menu_Bar = QtWidgets.QMenuBar(self)
        self.Menu_Bar.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed))
        self.Help_Menu = self.Menu_Bar.addMenu(u"帮助")
        self.Help_Action = QtWidgets.QAction(u"帮助文档", self)
        self.Help_Menu.addAction(self.Help_Action)
        self.Help_Action.triggered.connect(lambda: webbrowser.open_new_tab(
            'http://wiki.l0v0.com/PyToolkit/#/1_fbx_importer'))

        layout.addWidget(self.Menu_Bar)
        layout.addWidget(self.compare_splitter)
        layout.addWidget(self.import_button)

        # Note QSettings 记录加载路径
        directory = self.settings.value("assets_path")
        if directory:
            self.selector.line.setText(directory)
            self.update_list(directory)

    def refresh(self):
        # NOTE 获取目录下的资源
        assets = unreal.EditorAssetLibrary.list_assets(
            self.selector.line.text())

        # NOTE unreal asset 添加 帧数 tooltip
        for i, asset in enumerate(assets):
            anim = unreal.load_asset(asset)
            if not isinstance(anim, unreal.AnimSequence):
                continue
            frame_count = unreal.AnimationLibrary.get_num_frames(anim)
            item = self.asset_list.item(i)
            item.setToolTip(u"关键帧数: %s" % frame_count)
            item.frame_count = frame_count

        self.compare_assets()

    def handle_directory(self, directory=None):
        directory = directory if directory else QtWidgets.QFileDialog.getExistingDirectory(
            self)

        if not directory:
            return

        for file_name in IProgressDialog.loop(os.listdir(directory)):
            if not file_name.lower().endswith(".fbx"):
                continue
            self.fbx_list.addItem(os.path.join(directory, file_name))

    def get_file(self):
        path_list, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, caption=u"获取 FBX 文件", filter="FBX (*.fbx);;所有文件 (*)")
        for path in IProgressDialog.loop(path_list):
            self.fbx_list.addItem(path)

    def select_folder(self, line):
        selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
        if len(selected_assets) == 0:
            return
        asset = selected_assets[0]
        directory = unreal.Paths.get_path(asset.get_path_name())

        if directory:
            line.setText(directory)
            self.update_list(directory)
            self.settings.setValue("assets_path", directory)

    def update_list(self, directory):
        self.asset_list.clear()
        self.fbx_list.clear()
        # NOTE 获取目录下的资源
        assets = unreal.EditorAssetLibrary.list_assets(directory)

        # NOTE unreal asset 添加 帧数 tooltip
        for asset in assets:
            item = QtWidgets.QListWidgetItem()
            anim = unreal.load_asset(asset)
            if type(anim) is not unreal.AnimSequence:
                continue
            frame_count = unreal.AnimationLibrary.get_num_frames(anim)
            item.setText(asset)
            item.frame_count = frame_count
            item.setToolTip(u"关键帧数: %s" % frame_count)
            item.asset = anim
            self.asset_list.addItem(item)
            self.fbx_list.insertItem(0, "")

        # NOTE 添加空 item
        self.compare_assets()

    def compare_assets(self):

        style = QtWidgets.QApplication.style()
        error_icon = style.standardIcon(QtWidgets.QStyle.SP_MessageBoxCritical)
        apply_icon = style.standardIcon(QtWidgets.QStyle.SP_DialogApplyButton)

        # NOTE 获取未匹配的 FBX
        count = self.asset_list.count()
        asset_list = [self.asset_list.item(i).text() for i in range(count)]
        for i in range(count, self.fbx_list.count()):
            item = self.fbx_list.item(i)
            if not item:
                continue

            path = item.text()
            if not path:
                self.fbx_list.takeItem(i)
                continue

            fbx_name, _ = os.path.splitext(item.text())
            for j, asset in enumerate(asset_list):
                asset_name = asset.split(".")[-1]
                asset_name = asset_name.strip().lower()
                fbx_name = fbx_name.strip().lower()
                # print("%s <=> %s %s" % (fbx_name, asset_name,asset_name == fbx_name))
                if asset_name == fbx_name:
                    # NOTE 设置 item
                    compare_item = self.fbx_list.item(j)
                    compare_item.setText(item.text())
                    compare_item.setToolTip(item.toolTip())
                    compare_item.setIcon(error_icon)
                    compare_item.frame_count = item.frame_count
                    self.fbx_list.takeItem(i)
                    brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 0))
                    compare_item.setBackground(brush)
                    break

        # NOTE compare assets frame data
        for i in range(count):
            anim_item = self.asset_list.item(i)
            fbx_item = self.fbx_list.item(i)
            if fbx_item.text() and hasattr(fbx_item, "frame_count"):
                if anim_item.frame_count == fbx_item.frame_count:
                    fbx_item.setIcon(apply_icon)
                else:
                    fbx_item.setIcon(error_icon)


def main():
    global FBXImporter_win
    FBXImporter_win = FBXImporter_UI()
    FBXImporter_win.show()


if __name__ == "__main__":
    main()
