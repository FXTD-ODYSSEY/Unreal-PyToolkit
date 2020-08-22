# -*- coding: utf-8 -*-
"""
可以输入带提示的 下拉菜单 组件
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-07-18 21:09:23'


from ue_util import toast
from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import loadUi
import unreal
import sys
import os
MODULE = os.path.dirname(__file__)
sys.path.insert(0, MODULE) if MODULE not in sys.path else None


class USelector(QtWidgets.QWidget):
    _class_filter = []

    def __init__(self, parent=None, class_filter=None):
        super(USelector, self).__init__(parent)

        self.class_filter = class_filter
        DIR = os.path.dirname(__file__)
        ui_path = os.path.join(DIR, "ue_selector.ui")
        loadUi(ui_path, self)

        self.initilize()

    def initilize(self):
        # NOTE 设置图标
        style = QtWidgets.QApplication.style()
        icon = style.standardIcon(QtWidgets.QStyle.SP_ArrowBack)
        self.UGet.setIcon(icon)
        icon = style.standardIcon(QtWidgets.QStyle.SP_FileDialogContentsView)
        self.UFind.setIcon(icon)
        icon = style.standardIcon(QtWidgets.QStyle.SP_BrowserStop)
        self.UClear.setIcon(icon)

        self.USelector.popup.connect(self.list_asset)
        self.UGet.clicked.connect(self.get_asset)
        self.UFind.clicked.connect(self.sync_asset)
        self.UClear.clicked.connect(
            lambda: self.USelector.setCurrentIndex(self.USelector.count()-1))

        # TODO 无法获取 thunmnail 暂时隐藏
        self.UThumbnail.hide()

    @property
    def class_filter(self):
        return self._class_filter

    @class_filter.setter
    def class_filter(self, filter):
        self._class_filter = filter if isinstance(filter, list) else [
            filter] if filter else []
        if self._class_filter:
            self.list_asset()

    def filter_append(self, _filter):
        if not _filter:
            return
        elif isinstance(_filter, list):
            self._class_filter.extend(_filter)
        elif isinstance(_filter, dict):
            self._class_filter.extend(_filter.keys())
        else:
            self._class_filter.append(_filter)
        self.list_asset()

    def list_asset(self):
        reg = unreal.AssetRegistryHelpers.get_asset_registry()
        n_list = [c.__name__ for c in self.class_filter]
        ar_filter = unreal.ARFilter(class_names=n_list, recursive_classes=True)
        assets = reg.get_assets(ar_filter)
        assets_path = [str(a.object_path) for a in assets]

        self.USelector.clear()
        self.USelector.addItems(assets_path)
        self.USelector.addItem("None")
        return assets_path

    def get_asset(self):
        selected_asset = [a for a in unreal.EditorUtilityLibrary.get_selected_assets(
        ) for cls_type in self.class_filter if isinstance(a, cls_type)]

        if not selected_asset:
            toast(u'请选择下列类型\n %s' % (
                "\n".join([c.__name__ for c in self.class_filter])))
            return

        selected_asset = selected_asset[0]
        count = self.USelector.count()
        for i in range(count):
            text = self.USelector.itemText(i)
            if text == selected_asset.get_path_name():
                self.USelector.setCurrentIndex(i)
                break

    def sync_asset(self):
        path = self.USelector.currentText()
        unreal.EditorAssetLibrary.sync_browser_to_objects([path])


    def get_path(self):
        text = self.USelector.currentText()
        return None if text == "None" else text
    
def main():
    selector = USelector(class_filter=[unreal.Material])
    selector.show()


if __name__ == "__main__":
    main()
