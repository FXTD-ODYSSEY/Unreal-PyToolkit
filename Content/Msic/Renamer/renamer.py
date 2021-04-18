# -*- coding: utf-8 -*-
"""
批量重命名工具
- [x] 定位文件系统路径
- [x] 拖拽排序
- [x] 前后缀
- [x] 正则支持

- [x] 按照命名规范重命名
- [x] BUG 新名称重命名会丢失
- [x] BUG 挪动选择会丢失

- [x] QSettings 配置记录
- [x] 配置导入导出
- [x] 帮助文档

2021-3-31
- [x] 支持 actor 改名
- [x] 修复 PySide2 MinimumExpanding BUG
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-8-22 11:15:26'

import os
import re
import sys
import json
import webbrowser
from shutil import copyfile
from functools import partial
from collections import deque
from string import Template
if sys.version_info[0] == 2:
    from string import _multimap as ChainMap
else:
    from collections import ChainMap

import unreal

from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import load_ui, QFileDialog
from ue_util import error_log, toast
from dayu_widgets.item_model import MTableModel, MSortFilterModel

util_lib = unreal.EditorUtilityLibrary()
level_lib = unreal.EditorLevelLibrary()
asset_lib = unreal.EditorAssetLibrary()
sys_lib = unreal.SystemLibrary()

def get_convention():
    DIR = os.path.dirname(__file__)
    json_path = os.path.join(DIR, "convention.json")
    with open(json_path, 'r') as f:
        conventions = json.load(f, encoding='utf-8')
    return conventions

class ReplaceTemplate(Template):
    def substitute(*args, **kws):
        if not args:
            raise TypeError("descriptor 'substitute' of 'Template' object "
                            "needs an argument")
        self, args = args[0], args[1:]  # allow the "self" keyword be passed
        if len(args) > 1:
            raise TypeError('Too many positional arguments')
        if not args:
            mapping = kws
        elif kws:
            mapping = ChainMap(kws, args[0])
        else:
            mapping = args[0]
        # Helper function for .sub()

        def convert(mo):
            # Check the most common path first.
            named = mo.group('named') or mo.group('braced')
            if named is not None:
                # NOTE 修正默认 Templete 替换报错
                default = "%s{%s}" % (self.delimiter, named) if mo.group(
                    'braced') else "%s%s" % (self.delimiter, named)
                val = mapping.get(named, default)
                # We use this idiom instead of str() because the latter will
                # fail if val is a Unicode containing non-ASCII characters.
                return '%s' % (val,)
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                return self.delimiter
                # self._invalid(mo)
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)


class RenamerWinBase(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(RenamerWinBase, self).__init__(parent)
        DIR, file_name = os.path.split(__file__)
        file_name = os.path.splitext(file_name)[0]
        load_ui(os.path.join(DIR, "%s.ui" % file_name), self)

        # NOTE 获取 convention 数据
        self.conventions = get_convention()

        name = "%s.ini" % self.__class__.__name__
        self.settings = QtCore.QSettings(name, QtCore.QSettings.IniFormat)
        # NOTE 配置 MComboBox
        self.Search_LE.setPlaceholderText(u"输入关键字")
        self.Replace_LE.setPlaceholderText(u"输入替换文字")
        self.Export_Setting_Action.triggered.connect(self.export_setting)
        self.Import_Setting_Action.triggered.connect(self.import_setting)
        self.Help_Action.triggered.connect(lambda: webbrowser.open_new_tab(
            'http://wiki.l0v0.com/unreal/PyToolkit/#/msic/2_renamer'))
        self.Convention_Action.triggered.connect(lambda: webbrowser.open_new_tab(
            'https://github.com/Allar/ue4-style-guide'))

        # NOTE 隐藏左侧配置项
        self.Splitter.splitterMoved.connect(
            lambda: self.settings.setValue("splitter_size", self.Splitter.sizes()))
        splitter_size = self.settings.value("splitter_size")
        self.Splitter.setSizes(
            [int(i) for i in splitter_size] if splitter_size else [0, 1])

        # NOTE 配置 Header
        self.model = MTableModel()
        self.header_list = [
            {
                'label': data,
                'key': data,
                'bg_color': lambda x, y: y.get('bg_color', QtGui.QColor('transparent')),
                'tooltip': lambda x, y: y.get('asset').get_path_name(),
                'edit': lambda x, y: x or y.get('asset').get_name(),
                'display': lambda x, y: x or y.get('asset').get_name(),
                'editable': i == 1,
                'draggable': True,
                'width': 100,
            } for i, data in enumerate([u"原名称", u"新名称", u"文件类型"])
        ]
        self.model.set_header_list(self.header_list)
        self.model_sort = MSortFilterModel()
        self.model_sort.setSourceModel(self.model)

        self.Table_View.setModel(self.model_sort)
        self.Table_View.setShowGrid(True)
        header = self.Table_View.horizontalHeader()
        header.setStretchLastSection(True)
        
        self.setAcceptDrops(True)
        self.load_settings()

    def export_setting(self):
        path, _ = QFileDialog.getSaveFileName(
            self, caption=u"输出设置", filter=u"ini (*.ini)")
        if not path:
            return
        copyfile(self.settings.fileName(), path)
        toast(u"导出成功", "info")

    def import_setting(self):
        path, _ = QFileDialog.getOpenFileName(
            self, caption=u"获取设置", filter=u"ini (*.ini)")
        # NOTE 如果文件不存在则返回空
        if not path or not os.path.exists(path):
            return

        self.settings = QtCore.QSettings(path, QtCore.QSettings.IniFormat)
        self.settings.sync()
        self.load_settings()
        name = "%s.ini" % self.__class__.__name__
        self.settings = QtCore.QSettings(name, QtCore.QSettings.IniFormat)
        self.save_settings()
        toast(u"加载成功", "info")

    @staticmethod
    def check_loop(loop_list):
        for w in loop_list:
            name = w.objectName()
            if not hasattr(w, "objectName") or not name:
                continue
            elif isinstance(w, QtWidgets.QLineEdit) and not name.endswith("_LE"):
                continue
            elif isinstance(w, QtWidgets.QSpinBox) and not name.endswith("_SP"):
                continue
            elif isinstance(w, QtWidgets.QCheckBox) and not name.endswith("_CB"):
                continue
            elif isinstance(w, QtWidgets.QRadioButton) and not name.endswith("_RB"):
                continue
            elif isinstance(w, QtWidgets.QComboBox) and not name.endswith("_Combo"):
                continue
            yield w

    def save_settings(self):
        CB_list = self.findChildren(QtWidgets.QCheckBox)
        RB_list = self.findChildren(QtWidgets.QRadioButton)
        LE_list = self.findChildren(QtWidgets.QLineEdit)
        SP_list = self.findChildren(QtWidgets.QSpinBox)
        Combo_list = self.findChildren(QtWidgets.QComboBox)

        for B in self.check_loop(CB_list + RB_list):
            self.settings.setValue(B.objectName(), B.isChecked())

        for LE in self.check_loop(LE_list):
            self.settings.setValue(LE.objectName(), LE.text())

        for SP in self.check_loop(SP_list):
            self.settings.setValue(SP.objectName(), SP.value())

        for Combo in self.check_loop(Combo_list):
            index = Combo.currentIndex()
            self.settings.setValue(Combo.objectName(), index)

        # NOTE 获取 Table 记录
        data_list = self.model.get_data_list()
        asset_data = [data.get("asset").get_path_name() for data in data_list]
        self.settings.setValue("table_asset", asset_data)

    def load_settings(self):
        CB_list = self.findChildren(QtWidgets.QCheckBox)
        RB_list = self.findChildren(QtWidgets.QRadioButton)
        LE_list = self.findChildren(QtWidgets.QLineEdit)
        SP_list = self.findChildren(QtWidgets.QSpinBox)
        Combo_list = self.findChildren(QtWidgets.QComboBox)
        widget_dict = {}
        for B in self.check_loop(CB_list + RB_list):
            val = self.settings.value(B.objectName())
            if val is not None:
                val = True if str(val).lower() == "true" else False
                widget_dict[B.setChecked] = val

        for LE in self.check_loop(LE_list):
            val = self.settings.value(LE.objectName())
            if val is not None:
                widget_dict[LE.setText] = val

        for SP in self.check_loop(SP_list):
            val = self.settings.value(SP.objectName())
            if val is not None:
                widget_dict[SP.setValue] = int(val)

        for Combo in self.check_loop(Combo_list):
            val = self.settings.value(Combo.objectName())
            if val is not None:
                widget_dict[Combo.setCurrentIndex] = int(val)

        # NOTE 添加 data_list
        asset_data = self.settings.value("table_asset")
        # NOTE 批量设置属性值
        for setter, val in widget_dict.items():
            setter(val)
        if not asset_data:
            return
        
        actor_list = []
        asset_list = []
        for path in asset_data:
            asset = unreal.load_object(None,path)
            if isinstance(asset,unreal.Actor):
                actor_list.append(asset)
            elif asset_lib.does_asset_exist(path):
                asset_list.append(asset)

        data_list = self.model.get_data_list()
        
        data_list.extend([{
            'bg_color': QtGui.QColor("transparent"),
            'asset': asset,
            u"原名称": asset.get_name(),
            u"新名称": "",
            u"文件类型": type(asset).__name__,
        } for asset in asset_list])
        
        data_list.extend([{
            'bg_color': QtGui.QColor("transparent"),
            'asset': actor,
            u"原名称": actor.get_actor_label(),
            u"新名称": "",
            u"文件类型": type(actor).__name__,
        } for actor in actor_list])
                
            
        self.model.set_data_list(data_list)
        self.update_table()

    def dragEnterEvent(self, event):
        event.accept() if event.mimeData().hasUrls() else event.ignore()

    def dropEvent(self, event):
        # Note 获取拖拽文件的地址
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            print(event.mimeData().urls())
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def show(self):
        super(RenamerWinBase, self).show()

        # NOTE 配置 QGroupBox 的样式
        self.setStyleSheet(self.styleSheet() + """
        QGroupBox{
            border: 0.5px solid black;
            padding-top:10px;
        }
        """)

    def update_table(self):
        raise NotImplementedError


class UERenamerWin(RenamerWinBase):

    
    def get_icon_info(self):
        return {
            "Up":{
                "icon":QtWidgets.QStyle.SP_ArrowUp,
                "callback":lambda: self.move_item(up=True),
                "tooltip":u"上移",
            },
            "Dn":{
                "icon":QtWidgets.QStyle.SP_ArrowDown,
                "callback":lambda: self.move_item(up=False),
                "tooltip":u"下移",
            },
            "Del":{
                "icon":QtWidgets.QStyle.SP_BrowserStop,
                "callback":self.remove_items,
                "tooltip":u"删除文件",
            },
            "Find":{
                "icon":QtWidgets.QStyle.SP_FileDialogContentsView,
                "callback":self.locate_item_location,
                "tooltip":u"定位文件",
            },
            "Get_Asset":{
                "icon":QtWidgets.QStyle.SP_FileDialogStart,
                "callback":self.add_selected_assets,
                "tooltip":u"获取资产",
            },
            "Get_Actor":{
                "icon":QtWidgets.QStyle.SP_FileDialogListView,
                "callback":self.add_selected_actors,
                "tooltip":u"获取Actor",
            },
            "Drive":{
                "icon":QtWidgets.QStyle.SP_DriveHDIcon,
                "callback":self.locate_file_location,
                "tooltip":u"打开系统目录路径",
            },
            "Update":{
                "icon":QtWidgets.QStyle.SP_BrowserReload,
                "callback":self.update_table,
                "tooltip":u"刷新",
            },
            "Rename":{
                "icon":QtWidgets.QStyle.SP_DialogSaveButton,
                "callback":self.rename,
                "tooltip":u"批量改名",
            },
        }
        
    def __init__(self, parent=None):
        super(UERenamerWin, self).__init__(parent)
        
        # NOTE 设置按钮图标
        style = QtWidgets.QApplication.style()
        for typ,info in self.get_icon_info().items():
            icon = style.standardIcon(info.get("icon"))
            BTN = "%s_BTN" % typ
            if hasattr(self,BTN):
                BTN = getattr(self,BTN)
                BTN.setIcon(icon)
                BTN.clicked.connect(info.get("callback",lambda:None))
                tooltip = info.get("tooltip","")
                BTN.setToolTip('<span style="font-weight:600;">%s</span>' % tooltip)
                
            ACTION = "%s_Action" % typ
            getattr(self,ACTION).setIcon(icon) if hasattr(self,ACTION) else None
        icon = style.standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView)
        self.setWindowIcon(icon)
        
        # NOTE 添加 delete 键删除 
        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Del"), self)
        self.shortcut.activated.connect(self.remove_items)
        self.Search_LE.textChanged.connect(self.update_table)
        self.Replace_LE.textChanged.connect(self.update_table)

        # NOTE 设置内置变量启用
        for cb in self.Variable_Group.findChildren(QtWidgets.QCheckBox):
            cb.stateChanged.connect(self.update_table)
            self.Select_All_BTN.clicked.connect(partial(cb.setChecked, True))
            self.Toggle_Select_BTN.clicked.connect(cb.toggle)
            self.Non_Select_BTN.clicked.connect(partial(cb.setChecked, False))

        # NOTE 添加右键菜单
        self.Table_View.customContextMenuRequested.connect(
            lambda: self.Right_Menu.popup(QtGui.QCursor.pos()))

        # NOTE 运行添加 drop event
        self.Table_View.setDragEnabled(True)
        self.Table_View.setAcceptDrops(True)
        self.Table_View.viewport().setAcceptDrops(True)
        self.Table_View.setDragDropOverwriteMode(False)
        self.Table_View.setDropIndicatorShown(True)
        self.Table_View.dropEvent = self.tableDropEvent
        self.Table_View.dragEnterEvent = self.tableDragEnterEvent
        self.Table_View.dragMoveEvent = self.tableDragMoveEvent

    def tableDragEnterEvent(self, event):
        return event.accept()

    def tableDragMoveEvent(self, event):
        return event.accept()

    def tableDropEvent(self, event):
        if event.isAccepted() or event.source() != self.Table_View:
            return

        data_list = self.model.get_data_list()
        drop_row = self.drop_on(event)
        rows_to_move = []
        for item in sorted(self.Table_View.selectionModel().selectedRows(), reverse=True):
            row = item.row()
            rows_to_move.append(data_list.pop(row))
            if row < drop_row:
                drop_row -= 1

        # NOTE 移动数组
        idx_list = []
        for row_index, data in enumerate(reversed(rows_to_move)):
            row_index += drop_row
            idx_list.append(row_index)
            data_list.insert(row_index, data)

        self.model.set_data_list(data_list)

        # NOTE item 选择
        mode = QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows
        for idx in idx_list:
            self.Table_View.selectionModel().select(self.model.index(idx, 0), mode)
        self.update_table()

    def drop_on(self, event):
        index = self.Table_View.indexAt(event.pos())
        if not index.isValid():
            return self.model.rowCount()
        return index.row() + 1 if self.is_below(event.pos(), index) else index.row()

    def is_below(self, pos, index):
        rect = self.Table_View.visualRect(index)
        margin = 2
        if pos.y() - rect.top() < margin:
            return False
        elif rect.bottom() - pos.y() < margin:
            return True
        # noinspection PyTypeChecker
        return rect.contains(pos, True) and not (int(self.Table_View.model().flags(index)) & QtCore.Qt.ItemIsDropEnabled) and pos.y() >= rect.center().y()

    def remove_items(self):
        data_list = self.model.get_data_list()
        indexes = self.Table_View.selectionModel().selectedRows()
        if not indexes:
            return
        for index in sorted(indexes, reverse=True):
            data_list.pop(index.row())
        self.model.set_data_list(data_list)

    def move_item(self, up=False):

        data_list = self.model.get_data_list()
        indexes = self.Table_View.selectionModel().selectedRows()
        if not indexes:
            return
        idx_list = {}
        row_list = [index.row() for index in sorted(indexes, reverse=not up)]
        for row in row_list:
            idx = row-1 if up else row+1
            idx = len(data_list)-1 if idx == - \
                1 else 0 if idx == len(data_list) else idx
            idx_list[row] = idx

        if min(row_list) == 0 or max(row_list) == len(data_list)-1:
            # NOTE 数组边界上通过 rotate 进行无缝移动 | https://stackoverflow.com/questions/2150108
            data_list = deque(data_list)
            data_list.rotate(-1 if up else 1)
            data_list = list(data_list)
        else:
            for row in row_list:
                idx = idx_list.get(row)
                data_list.insert(idx, data_list.pop(row))

        self.model.set_data_list(data_list)
        mode = QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows
        self.update_table()
        for row, idx in idx_list.items():
            self.Table_View.selectionModel().select(self.model.index(idx, 0), mode)

    # NOTE ----------------------------------------------------------------

    def getAlpha(self, value, capital=False):
        # NOTE 从 DT Advance PyQt 教程 截取下来的代码
        ''' Convert an integer value to a character. a-z then double, aa-zz etc. '''

        # calculate number of characters required
        #
        base_power = base_start = base_end = 0
        while value >= base_end:
            base_power += 1
            base_start = base_end
            base_end += pow(26, base_power)
        base_index = value - base_start

        # create alpha representation
        #
        alphas = ['a'] * base_power
        for index in range(base_power - 1, -1, -1):
            alphas[index] = chr(97 + (base_index % 26))
            base_index /= 26

        if capital:
            return ''.join(alphas).upper()
        return ''.join(alphas)

    def get_index(self, i):
        index = self.Index_Combo.currentIndex()
        if index == 0:
            padding = self.Padding_SP.value()
            return str(i).zfill(padding)
        elif index == 1:
            check = self.Upper_CB.isChecked()
            letter = self.getAlpha(i, check)
            return letter

    def handle_replace(self, i, data, replace):
        var_dict = {}
        prefix = self.Prefix_LE.text() if self.Prefix_CB.isChecked() else ""
        suffix = self.Suffix_LE.text() if self.Suffix_CB.isChecked() else ""

        asset = data["asset"]
        path = asset.get_path_name()

        if self.INDEX_CB.isChecked():
            var_dict["INDEX"] = self.get_index(i)

        if self.ORIGIN_NAME_CB.isChecked():
            var_dict["ORIGIN_NAME"] = os.path.splitext(
                os.path.basename(path))[0]

        if self.MATCH_CB.isChecked():
            var_dict["MATCH"] = replace

        if self.ASSET_PATH_CB.isChecked():
            var_dict["ASSET_PATH"] = path

        if self.ASSET_FILE_PATH_CB.isChecked():
            project = sys_lib.get_project_content_directory()
            var_dict["ASSET_FILE_PATH"] = path.replace("/Game/", project)

        type_name = type(asset).__name__
        if self.ASSET_CLASS_LONG_CB.isChecked():
            var_dict["ASSET_CLASS_LONG"] = type_name

        if self.ASSET_CLASS_CB.isChecked():
            convention = self.conventions.get(type_name, type_name)
            if isinstance(convention, dict):
                convention = convention.get("prefix", type_name)
            var_dict["ASSET_CLASS"] = convention

        if self.FOLDER_PATH_CB.isChecked():
            var_dict["FOLDER_PATH"] = os.path.basename(os.path.dirname(path))

        prefix = ReplaceTemplate(prefix).substitute(**var_dict)
        suffix = ReplaceTemplate(suffix).substitute(**var_dict)
        replace = ReplaceTemplate(replace).substitute(**var_dict)

        return replace, prefix, suffix

    def handle_convention(self, data):
        asset = data["asset"]
        name = asset.get_name()
        type_name = type(asset).__name__
        convention = self.conventions.get(type_name, type_name)
        if isinstance(convention, dict):
            prefix = convention.get("prefix", "")
            suffix = convention.get("suffix", "")
        else:
            prefix = convention
            suffix = ""
        if name.startswith(prefix):
            prefix = ""
        if name.endswith(suffix):
            suffix = ""
        return "%s%s%s" % (prefix, name, suffix)

    @QtCore.Slot()
    def update_table(self):
        data_list = self.model.get_data_list()
        for i, data in enumerate(data_list[:]):
            asset = data["asset"]
            try:
                name = asset.get_name()
            except:
                data_list.pop(i)
                self.update_table()
                return

            path = asset.get_path_name()
            search = self.Search_LE.text()
            replace = self.Replace_LE.text()

            if not unreal.load_object(None,path):
                data_list.pop(i)
                self.update_table()
                return

            if not self.RE_CB.isChecked():
                search = re.escape(search)

            if self.Convention_CB.isChecked():
                name = self.handle_convention(data)

            flags = re.I if self.Ignore_Case_CB.isChecked() else 0
            replace, prefix, suffix = self.handle_replace(i, data, replace)
            try:
                reg = re.compile(search, flags)
                replace = reg.sub(replace, name)
            except:
                search = False
            if search and reg.search(name):
                data[u'新名称'] = "%s%s%s" % (prefix, replace, suffix)
                data["bg_color"] = QtGui.QColor("purple")
            else:
                data[u'新名称'] = "%s%s%s" % (prefix, name, suffix)
                data["bg_color"] = QtGui.QColor("transparent")

        self.model.set_data_list(data_list)
        self.save_settings()

    def locate_file_location(self):
        data_list = self.model.get_data_list()
        index = self.Table_View.selectionModel().currentIndex()
        if not index:
            toast(u"没有选择元素进行定位")
            return

        asset = data_list[index.row()]["asset"]
        path = asset.get_path_name()
        # path = os.path.splitext(path)[0]

        project = sys_lib.get_project_content_directory()
        path = path.replace("/Game/", project)
        path = os.path.dirname(path)
        if os.path.exists(path):
            os.startfile(path)
        else:
            toast(u"当前选择元素路径不存在")

    def locate_item_location(self):
        data_list = self.model.get_data_list()
        index = self.Table_View.selectionModel().currentIndex()
        if not index:
            toast(u"没有选择元素进行定位")
            return
        asset = data_list[index.row()]["asset"]
        path = asset.get_path_name()
        if asset_lib.does_asset_exist(path):
            asset_lib.sync_browser_to_objects([path])
        else:
            toast(u"元素不存在")

    def rename(self):

        data_list = self.model.get_data_list()
        for i, data in enumerate(data_list[:]):
            asset = data['asset']
            new_name = data[u'新名称']
            # NOTE 文件被删除
            try:
                name = asset.get_name()
            except:
                data_list.pop(i)
                continue

            path = asset.get_path_name()
            if isinstance(asset,unreal.Actor):
                data[u'原名称'] = new_name
                asset.set_actor_label(new_name)
            else:
                if not asset_lib.does_asset_exist(path):
                    data_list.pop(i)
                else:
                    if new_name != name:
                        data[u'原名称'] = new_name
                        util_lib.rename_asset(asset, new_name)

        self.model.set_data_list(data_list)
        self.update_table()

    def add_selected_assets(self):
        data_list = self.model.get_data_list()
        tooltip_list = [data.get("asset").get_path_name()
                        for data in data_list]
        
        asset_list = [asset for asset in util_lib.get_selected_assets()
                      if asset.get_path_name() not in tooltip_list]
        
        if not asset_list:
            toast(u"请选择资产")
            return
        
        # NOTE 确保不添加重复的 item
        data_list.extend([{
            'bg_color': QtGui.QColor("transparent"),
            'asset': asset,
            u"原名称": asset.get_name(),
            u"新名称": "",
            u"文件类型": type(asset).__name__,
        } for asset in asset_list])
        
        self.update_table()
        self.model.set_data_list(data_list)

    def add_selected_actors(self):
        data_list = self.model.get_data_list()
        tooltip_list = [data.get("asset").get_path_name()
                        for data in data_list]
        
        actor_list = [actor for actor in level_lib.get_selected_level_actors()
                      if actor.get_path_name() not in tooltip_list]
        
        if not actor_list:
            toast(u"请选择Actor")
            return
        
        data_list.extend([{
            'bg_color': QtGui.QColor("transparent"),
            'asset': actor,
            u"原名称": actor.get_actor_label(),
            u"新名称": "",
            u"文件类型": type(actor).__name__,
        } for actor in actor_list])
        
        
        self.update_table()
        self.model.set_data_list(data_list)


@error_log
def main():
    Renamer = UERenamerWin()
    Renamer.show()

if __name__ == "__main__":
    main()
