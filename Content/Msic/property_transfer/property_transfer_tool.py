# -*- coding: utf-8 -*-
"""
属性批量传递工具
- [x] TreeView
- [x] Overlay 组件
- [x] 过滤接入
- [x] 选择资产属性配置颜色

- [x] 右键菜单
- [ ] ~勾选属性导出导入~
- [ ] ~蓝图属性复制~

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2021-04-01 20:12:44"

import os
import sys
import webbrowser

from collections import defaultdict
from functools import partial

import unreal

from QBinder import BinderTemplate
from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import load_ui
from ue_util import error_log, toast
from dayu_widgets.item_model import MTableModel, MSortFilterModel

level_lib = unreal.EditorLevelLibrary()
util_lib = unreal.EditorUtilityLibrary()
asset_lib = unreal.EditorAssetLibrary()
sys_lib = unreal.SystemLibrary()
mat_lib = unreal.MaterialEditingLibrary()

py_lib = unreal.PyToolkitBPLibrary()
DIR = os.path.dirname(__file__)


def cast(typ, obj):
    try:
        return getattr(unreal, typ).cast(obj)
    except:
        return None


@error_log
class MaterialTransfer(object):
    def _get_material_paramters(self, expressions):
        """
        inspire by https://github.com/20tab/UnrealEnginePython/issues/103
        """
        paramters = defaultdict(set)
        for expresion in expressions:
            func = cast("MaterialExpressionMaterialFunctionCall", expresion)
            if func:
                func = func.get_editor_property("material_function")
                expressions = py_lib.get_material_function_expressions(func)
                params = self._get_material_paramters(expressions)
                for group, param in params.items():
                    for p in param:
                        paramters[str(group)].add(str(p))
                continue

            param = cast("MaterialExpressionParameter", expresion)
            if not param:
                param = cast("MaterialExpressionTextureSampleParameter", expresion)
            if not param:
                param = cast("MaterialExpressionFontSampleParameter", expresion)

            if param:
                group = param.get_editor_property("group")
                parameter_name = param.get_editor_property("parameter_name")
                paramters[str(group)].add(str(parameter_name))

        return paramters

    def get_material_property(self, material):
        scalars = mat_lib.get_scalar_parameter_names(material)
        vectors = mat_lib.get_vector_parameter_names(material)
        switches = mat_lib.get_static_switch_parameter_names(material)
        textures = mat_lib.get_texture_parameter_names(material)

        parent_material = material.get_base_material()

        expressions = py_lib.get_material_expressions(parent_material)
        paramters = self._get_material_paramters(expressions)

        collections = defaultdict(dict)
        for grp, params in sorted(paramters.items()):
            for p in sorted(params):
                value = None
                if p in textures:
                    func = mat_lib.get_material_instance_texture_parameter_value
                    value = func(material, p)
                    value = value.get_path_name()
                elif p in switches:
                    value = mat_lib.get_material_instance_static_switch_parameter_value(
                        material, p
                    )
                elif p in vectors:
                    func = mat_lib.get_material_instance_vector_parameter_value
                    value = func(material, p)
                    value = "|".join(
                        [
                            "%s : %-10s" % (c.upper(), round(getattr(value, c), 2))
                            for c in "rgba"
                        ]
                    )
                elif p in scalars:
                    func = mat_lib.get_material_instance_scalar_parameter_value
                    value = func(material, p)

                collections[grp][p] = value

        return collections

    def update_material_property(self, material):
        scalars = mat_lib.get_scalar_parameter_names(material)
        vectors = mat_lib.get_vector_parameter_names(material)
        switches = mat_lib.get_static_switch_parameter_names(material)
        textures = mat_lib.get_texture_parameter_names(material)
        all_params = []
        all_params.extend(scalars)
        all_params.extend(vectors)
        all_params.extend(switches)
        all_params.extend(textures)

        property_list = self.property_model.get_data_list()

        for group in property_list:
            green_list = []
            red_list = []
            children = group.get("children")
            children_count = len(children)
            for prop in children:
                prop["bg_color"] = QtGui.QColor("transparent")
                if not prop.get("property_checked"):
                    continue

                attr = prop.get("property")
                if attr in all_params:
                    green_list.append(attr)
                    prop["bg_color"] = QtGui.QColor("green")
                else:
                    red_list.append(attr)
                    prop["bg_color"] = QtGui.QColor("red")

            if len(green_list) == children_count:
                group["bg_color"] = QtGui.QColor("green")
            elif len(red_list) == children_count:
                group["bg_color"] = QtGui.QColor("red")
            elif not green_list and not red_list:
                group["bg_color"] = QtGui.QColor("transparent")
            else:
                group["bg_color"] = QtGui.QColor("yellowgreen")

        # NOTE 更新界面
        QtCore.QTimer.singleShot(0, self.repaint)

    def transfer_material_property(self, material, property_list):
        scalars = mat_lib.get_scalar_parameter_names(material)
        vectors = mat_lib.get_vector_parameter_names(material)
        switches = mat_lib.get_static_switch_parameter_names(material)
        textures = mat_lib.get_texture_parameter_names(material)

        for p in property_list:
            if p in textures:
                getter = mat_lib.get_material_instance_texture_parameter_value
                setter = mat_lib.set_material_instance_texture_parameter_value
                setter(material, p, getter(self.source, p))
            elif p in switches:
                getter = mat_lib.get_material_instance_static_switch_parameter_value
                setter = py_lib.set_material_instance_static_switch_parameter_value
                setter(material, p, getter(self.source, p))
            elif p in vectors:
                getter = mat_lib.get_material_instance_vector_parameter_value
                setter = mat_lib.set_material_instance_vector_parameter_value
                setter(material, p, getter(self.source, p))
            elif p in scalars:
                getter = mat_lib.get_material_instance_scalar_parameter_value
                setter = mat_lib.set_material_instance_scalar_parameter_value
                setter(material, p, getter(self.source, p))


@error_log
class AssetList(object):
    def locate_file_location(self):
        data_list = self.asset_model.get_data_list()
        index = self.Asset_List.selectionModel().currentIndex()
        if not index or not data_list:
            toast(u"没有元素可定位")
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
            toast(u"当前路径不存在")

    def locate_asset_location(self):
        data_list = self.asset_model.get_data_list()
        index = self.Asset_List.selectionModel().currentIndex()
        if not index or not data_list:
            toast(u"没有元素可定位")
            return
        asset = data_list[index.row()]["asset"]
        path = asset.get_path_name()
        if asset_lib.does_asset_exist(path):
            asset_lib.sync_browser_to_objects([path])
        else:
            toast(u"元素不存在")

    def remove_assets(self):
        data_list = self.asset_model.get_data_list()
        indexes = self.Asset_List.selectionModel().selectedRows()
        if not indexes or not data_list:
            return
        for index in sorted(indexes, reverse=True):
            data_list.pop(index.row())
        self.asset_model.set_data_list(data_list)


class PropertyTransferBinder(BinderTemplate):
    def __init__(self):
        dumper = self("dumper")
        dumper.set_auto_load(False)
        self.source_eanble = False
        self.lable_visible = False
        self.lable_text = ""


@error_log
class PropertyTransferTool(QtWidgets.QWidget, MaterialTransfer, AssetList):

    state = PropertyTransferBinder()

    def update_icon(self):
        data = {
            "Del": {
                "icon": QtWidgets.QStyle.SP_BrowserStop,
                "callback": self.remove_assets,
                "tooltip": u"删除文件",
            },
            "Locate": {
                "icon": QtWidgets.QStyle.SP_FileDialogContentsView,
                "callback": self.locate_asset_location,
                "tooltip": u"定位文件",
            },
            "Drive": {
                "icon": QtWidgets.QStyle.SP_DriveHDIcon,
                "callback": self.locate_file_location,
                "tooltip": u"打开系统目录路径",
            },
            "Expand": {
                "icon": QtWidgets.QStyle.SP_ToolBarVerticalExtensionButton,
                "callback": self.Property_Tree.expandAll,
                "tooltip": u"扩展全部",
            },
            "Collapse": {
                "icon": QtWidgets.QStyle.SP_ToolBarHorizontalExtensionButton,
                "callback": self.Property_Tree.collapseAll,
                "tooltip": u"收缩全部",
            },
            "Source_Locate": {
                "icon": QtWidgets.QStyle.SP_FileDialogContentsView,
                "callback": lambda: asset_lib.sync_browser_to_objects(
                    [self.source.get_path_name()]
                ),
                "tooltip": u"定位复制源",
            },
        }

        widget_dict = {
            "BTN": "clicked",
            "Action": "triggered",
        }

        style = QtWidgets.QApplication.style()
        icon = style.standardIcon(QtWidgets.QStyle.SP_BrowserReload)
        self.setWindowIcon(icon)
        for typ, info in data.items():
            icon = style.standardIcon(info.get("icon"))
            tooltip = info.get("tooltip", "")
            tooltip = '<span style="font-weight:600;">%s</span>' % tooltip
            callback = info.get("callback", lambda *args: None)

            for widget, signal in widget_dict.items():
                widget = "%s_%s" % (typ, widget)
                if hasattr(self, widget):
                    widget = getattr(self, widget)
                    widget.setIcon(icon)
                    getattr(widget, signal).connect(callback)
                    widget.setToolTip(tooltip)
                    widget.setEnabled(lambda: self.state.source_eanble)
                    widget.setEnabled(self.state.source_eanble)
                    # print(widget.isEnabled())

        # QtCore.QTimer.singleShot(0, lambda: self.state.source_eanble >> Set(False))

    def __init__(self, parent=None):
        super(PropertyTransferTool, self).__init__(parent)
        DIR, file_name = os.path.split(__file__)
        file_name = os.path.splitext(file_name)[0]
        load_ui(os.path.join(DIR, "%s.ui" % file_name), self)

        self.source = None

        help_link = "http://redarttoolkit.pages.oa.com/docs/posts/85c3f876.html"
        self.Help_Action.triggered.connect(lambda: webbrowser.open_new_tab(help_link))

        # NOTE 设置按钮图标
        QtCore.QTimer.singleShot(0, self.update_icon)

        menu_callback = lambda: self.Asset_Menu.popup(QtGui.QCursor.pos())
        self.Asset_List.customContextMenuRequested.connect(menu_callback)
        menu_callback = lambda: self.Property_Menu.popup(QtGui.QCursor.pos())
        self.Property_Tree.customContextMenuRequested.connect(menu_callback)

        self.Asset_Label.setVisible(lambda: self.state.lable_visible)
        self.Asset_Label.setText(lambda: self.state.lable_text)

        self.Src_BTN.clicked.connect(self.get_source)
        self.Dst_BTN.clicked.connect(self.get_destination)
        self.Transfer_BTN.clicked.connect(self.transfer_property)

        # NOTE 配置 splitter
        name = "%s.ini" % self.__class__.__name__
        self.settings = QtCore.QSettings(name, QtCore.QSettings.IniFormat)
        self.Splitter.splitterMoved.connect(
            lambda: self.settings.setValue("splitter_size", self.Splitter.sizes())
        )
        splitter_size = self.settings.value("splitter_size")
        size = [int(i) for i in splitter_size] if splitter_size else [700, 200]
        self.Splitter.setSizes(size)

        # NOTE 配置搜索栏
        self.Dst_Filter_LE.search()
        self.Dst_Filter_LE.setPlaceholderText("")
        self.Prop_Filter_LE.search()
        self.Prop_Filter_LE.setPlaceholderText("")

        # NOTE 配置 Property_Tree
        self.property_model = MTableModel()
        columns = {u"property": "属性名", u"value": "数值"}
        self.property_header_list = [
            {
                "label": label,
                "key": key,
                "bg_color": lambda x, y: y.get("bg_color", QtGui.QColor("transparent")),
                "checkable": i == 0,
                "searchable": True,
                "width": 300,
                "font": lambda x, y: {"bold": True},
            }
            for i, (key, label) in enumerate(columns.items())
        ]
        self.property_model.set_header_list(self.property_header_list)
        self.property_model_sort = MSortFilterModel()
        self.property_model_sort.set_header_list(self.property_header_list)
        self.property_model_sort.setSourceModel(self.property_model)
        self.Prop_Filter_LE.textChanged.connect(
            self.property_model_sort.set_search_pattern
        )

        self.Property_Tree.setModel(self.property_model_sort)
        header = self.Property_Tree.header()
        header.setStretchLastSection(True)

        # NOTE 配置 Asset_List
        self.asset_model = MTableModel()
        self.asset_header_list = [
            {
                "label": "destination",
                "key": "destination",
                "bg_color": lambda x, y: y.get("bg_color", QtGui.QColor("transparent")),
                "tooltip": lambda x, y: y.get("asset").get_path_name(),
                "checkable": True,
                "searchable": True,
                "width": 300,
                "font": lambda x, y: {"bold": True},
            }
        ]
        self.asset_model.set_header_list(self.asset_header_list)
        self.asset_model_sort = MSortFilterModel()
        self.asset_model_sort.search_reg.setPatternSyntax(QtCore.QRegExp.RegExp)
        self.asset_model_sort.set_header_list(self.asset_header_list)
        self.asset_model_sort.setSourceModel(self.asset_model)
        self.Dst_Filter_LE.textChanged.connect(self.asset_model_sort.set_search_pattern)

        self.Asset_List.setModel(self.asset_model_sort)
        self.Asset_List.selectionModel().selectionChanged.connect(
            self.asset_selection_change
        )
        self.property_model.dataChanged.connect(self.asset_selection_change)

    def get_source(self):
        assets = util_lib.get_selected_assets()
        if len(assets) < 1:
            toast(u"请选择一个资产")
            return

        asset = assets[0]
        self.set_property_tree(asset)
        self.asset_model.set_data_list([])
        self.property_model_sort.sort(0, QtCore.Qt.AscendingOrder)

    def get_destination(self):
        if not self.source:
            toast(u"请拾取复制源")
            return

        data_list = self.asset_model.get_data_list()
        tooltip_list = [data.get("asset").get_path_name() for data in data_list]

        assets = [
            asset
            for asset in util_lib.get_selected_assets()
            if isinstance(asset, type(self.source))
            and asset.get_path_name() not in tooltip_list
        ]

        if not assets:
            toast(u"请选择匹配的资产")
            return

        data_list.extend(
            [
                {
                    "bg_color": QtGui.QColor("transparent"),
                    "asset": asset,
                    "destination": asset.get_name(),
                    # NOTE 默认勾选
                    "destination_checked": QtCore.Qt.Checked,
                }
                for asset in assets
                if not asset is self.source
            ]
        )

        self.asset_model.set_data_list(data_list)

    def asset_selection_change(self, *args):
        model = self.Asset_List.selectionModel()
        indexes = model.selectedRows()
        if not indexes:
            return
        index = indexes[0]
        data_list = self.asset_model.get_data_list()
        data = data_list[index.row()]
        asset = data.get("asset")
        if isinstance(asset, unreal.MaterialInterface):
            self.update_material_property(asset)

    def set_property_tree(self, asset):
        if isinstance(asset, unreal.MaterialInterface):
            data = self.get_material_property(asset)
        elif isinstance(asset, unreal.Blueprint):
            pass
        else:
            toast(u"不支持资产")
            return

        data_list = [
            {
                "property": group,
                "value": "",
                "children": [
                    {
                        "bg_color": QtGui.QColor("transparent"),
                        "property": prop,
                        "property_checked": QtCore.Qt.Unchecked,
                        "value": value,
                    }
                    for prop, value in props.items()
                ],
            }
            for group, props in data.items()
        ]
        self.property_model.set_data_list(data_list)

        self.source = asset
        self.state.source_eanble = True
        self.state.lable_visible = True
        self.state.lable_text = asset.get_name()

    def transfer_property(self):

        for i, asset in enumerate(self.asset_model.get_data_list()):
            if not asset.get("destination_checked"):
                continue

            # NOTE 选择 Asset_List 的资产 更新颜色
            index = self.asset_model.index(i, 0)
            model = self.Asset_List.selectionModel()
            model.setCurrentIndex(index, model.SelectCurrent)

            property_list = [
                prop.get("property")
                for grp in self.property_model.get_data_list()
                for prop in grp.get("children")
                # NOTE 过滤没有勾选的资源
                if prop.get("bg_color") == QtGui.QColor("green")
                and prop.get("property_checked")
            ]

            # NOTE 传递属性
            asset = asset.get("asset")
            if isinstance(asset, type(self.source)):
                self.transfer_material_property(asset, property_list)
            else:
                raise RuntimeError(u"%s 和复制源类型不匹配" % asset.get_name())

        toast("传递完成",'success')


if __name__ == "__main__":
    widget = PropertyTransferTool()
    widget.show()
