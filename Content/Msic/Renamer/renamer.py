# -*- coding: utf-8 -*-
"""
特效资源导入配置面板
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-08-10 21:38:57'

import os
import sys
import webbrowser
from functools import partial

import unreal

from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import load_ui
from UE_Util import error_log, toast
from dayu_widgets.item_model import MTableModel, MSortFilterModel

util_lib = unreal.EditorUtilityLibrary()
asset_lib = unreal.EditorAssetLibrary()


class RenamerWinBase(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(RenamerWinBase, self).__init__(parent)
        DIR, file_name = os.path.split(__file__)
        file_name = os.path.splitext(file_name)[0]
        load_ui(os.path.join(DIR, "%s.ui" % file_name), self)

        # NOTE 配置 MComboBox
        self.Search_LE.lineEdit().setReadOnly(False)
        self.Replace_LE.lineEdit().setReadOnly(False)
        self.Search_LE.lineEdit().setPlaceholderText(u"输入关键字")
        self.Replace_LE.lineEdit().setPlaceholderText(u"输入替换文字")

        # NOTE 隐藏左侧配置项
        self.Splitter.setCollapsible(1, False)
        self.Splitter.setSizes([0, 1])

        # NOTE 配置 Header
        self.model = MTableModel()
        self.header_list = [
            {
                'label': data,
                'key': data,
                'bg_color': lambda *args: args[0].get('bg_color', QtGui.QColor(0, 0, 0, 0)) if isinstance(args[0], dict) else QtGui.QColor(0, 0, 0, 0),
                'tooltip': lambda *args: args[0].get('tooltip',args[0]) if isinstance(args[0], dict) else args[0],
                'editable': i == 1,
                'draggable': True,
                'width': 100,
            } for i, data in enumerate([u"原名称", u"新名称", u"文件类型"])
        ]
        self.model.set_header_list(self.header_list)
        self.model_sort = MSortFilterModel()
        self.model_sort.setSourceModel(self.model)

        self.Table_View.setShowGrid(True)
        self.Table_View.setModel(self.model_sort)
        header = self.Table_View.horizontalHeader()
        header.setStretchLastSection(True)

        # NOTE 运行添加 drop event
        self.setAcceptDrops(True)
        

    def dragEnterEvent(self, event):
        event.accept() if event.mimeData().hasUrls() else event.ignore()

    def dropEvent(self, event):
        # Note 获取拖拽文件的地址
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            print(event.mimeData().urls())
            # for url in IProgressDialog.loop(event.mimeData().urls()):
            #     path = (url.toLocalFile())
            #     _, ext = os.path.splitext(path)
            #     # Note 过滤已有的路径
            #     if ext.lower() in self.file_filter or "*" in self.file_filter:
            #         self.addItem(path)
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

class UERenamerWin(RenamerWinBase):
    
    def __init__(self, parent=None):
        super(UERenamerWin, self).__init__(parent)
        
        style = QtWidgets.QApplication.style()
        icon = style.standardIcon(QtWidgets.QStyle.SP_ArrowUp)
        self.Up_BTN.setIcon(icon)
        icon = style.standardIcon(QtWidgets.QStyle.SP_ArrowDown)
        self.Dn_BTN.setIcon(icon)
        icon = style.standardIcon(QtWidgets.QStyle.SP_BrowserStop)
        self.Del_BTN.setIcon(icon)
        icon = style.standardIcon(QtWidgets.QStyle.SP_FileDialogContentsView)
        self.Find_BTN.setIcon(icon)
        icon = style.standardIcon(QtWidgets.QStyle.SP_FileDialogStart)
        self.Get_BTN.setIcon(icon)
        
        self.Get_BTN.clicked.connect(self.add_selected_asset)
        self.Find_BTN.clicked.connect(self.locate_item_location)
        self.Del_BTN.clicked.connect(self.remove_items)
        self.Up_BTN.clicked.connect(lambda:self.move_item(up=True))
        self.Dn_BTN.clicked.connect(lambda:self.move_item(up=False))
        
        self.Locate_Widget.hide()
        self.Rename_BTN.clicked.connect(self.rename)
        self.Search_LE.lineEdit().textChanged.connect(self.update_table)
        self.Replace_LE.lineEdit().textChanged.connect(self.update_table)


        self.create_menu()
        
        # NOTE 添加右键菜单
        self.Table_View.customContextMenuRequested.connect(
            lambda: self.menu.popup(QtGui.QCursor.pos()))
    
    def create_menu(self):
        self.menu = QtWidgets.QMenu(self)

        add_selected_action = QtWidgets.QAction(u'添加当前选择', self)
        add_selected_action.triggered.connect(self.add_selected_asset)

        locate_file_action = QtWidgets.QAction(u'定位文件', self)
        locate_file_action.triggered.connect(self.locate_item_location)

        remove_action = QtWidgets.QAction(u'删除选择', self)
        remove_action.triggered.connect(self.remove_items)

        self.menu.addAction(add_selected_action)
        self.menu.addSeparator()
        self.menu.addAction(locate_file_action)
        self.menu.addAction(remove_action)
        
    def remove_items(self):
        data_list = self.model.get_data_list()
        indexes = self.Table_View.selectionModel().selectedRows()
        if not indexes:
            return
        for index in sorted(indexes, reverse=True):
            data_list.pop(index.row())
        self.model.set_data_list(data_list)

    def move_item(self,up=False):
        data_list = self.model.get_data_list()
        indexes = self.Table_View.selectionModel().selectedRows()
        if not indexes:
            return
        idx_list = []
        row_list = [index.row() for index in sorted(indexes, reverse=not up)]
        if min(row_list) == 0 and max(row_list) == len(data_list)-1:
            row_list = sorted(row_list, reverse=up)
            
        for row in row_list:
            idx = row-1 if up else row+1
            idx = len(data_list)-1 if idx == -1 else 0 if idx == len(data_list) else idx
            idx_list.append(idx)
            print([row,idx])
            data_list.insert(idx,data_list.pop(row))
        
        self.model.set_data_list(data_list)
        mode = QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows
        for idx in idx_list:
            self.Table_View.selectionModel().select(self.model.index(idx,0),mode)
            
        self.update_table()
        
    def update_table(self):
        search = self.Search_LE.lineEdit().text()
        if not search:
            return
        replace = self.Replace_LE.lineEdit().text()

        data_list = self.model.get_data_list()
        for i, data in enumerate(data_list[:]):
            name = data[u"原名称"]["name"]
            path = data[u"原名称"]["tooltip"]
            if not asset_lib.does_asset_exist(path):
                data_list.pop(i)
            elif search in name:
                data[u'新名称']["name"] = name.replace(search, replace)
                for header in data:
                    data[header]["bg_color"] = QtGui.QColor("purple")
            else:
                data[u'新名称']["name"] = name
                for header in data:
                    data[header]["bg_color"] = QtGui.QColor(0,0,0,0)

        self.model.set_data_list(data_list)

    def locate_item_location(self):
        data_list = self.model.get_data_list()
        index = self.Table_View.selectionModel().currentIndex()
        if not index:
            return 
        path = data_list[index.row()][u"原名称"]["tooltip"]
        if asset_lib.does_asset_exist(path):
            asset_lib.sync_browser_to_objects([path])

    def rename(self):
        data_list = self.model.get_data_list()
        for i, data in enumerate(data_list[:]):
            name = data[u"原名称"]["name"]
            path = data[u"原名称"]["tooltip"]
            if not asset_lib.does_asset_exist(path):
                data_list.pop(i)
            else:
                asset = unreal.load_asset(path)
                util_lib.rename_asset(asset, data[u'新名称']["name"])
                data[u"原名称"]["name"] = asset.get_name()
                data[u"原名称"]["tooltip"] = asset.get_path_name()

        self.model.set_data_list(data_list)
        self.update_table()

    def add_selected_asset(self):
        data_list = self.model.get_data_list()
        tooltip_list = [data.get(u"原名称").get("tooltip") for data in data_list]
        asset_list = [asset for asset in util_lib.get_selected_assets()
            if asset.get_path_name() not in tooltip_list]
        if not asset_list:
            return
        # NOTE 确保不添加重复的 item
        data_list.extend([{
            u"原名称": {
                "name": asset.get_name(),
                "tooltip": asset.get_path_name(),
            },
            u"新名称": {
                "name": ""
            },
            u"文件类型": {
                "name": type(asset).__name__
            },
        } for asset in asset_list])
        self.model.set_data_list(data_list)
        self.update_table()

@error_log
def main():
    Renamer = UERenamerWin()
    Renamer.show()


if __name__ == "__main__":
    main()
