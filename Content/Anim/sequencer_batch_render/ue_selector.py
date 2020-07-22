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

from dayu_widgets.message import MMessage
from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import loadUi
import unreal
import sys
import os
MODULE = os.path.dirname(__file__)
sys.path.insert(0, MODULE) if MODULE not in sys.path else None


class USelector(QtWidgets.QWidget):

    def __init__(self, parent=None, class_filter=None):
        super(USelector, self).__init__(parent)

        self.class_filter = class_filter if isinstance(
            class_filter, list) else []
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

        self.list_asset()
        self.USelector.popup.connect(self.list_asset)
        self.UGet.clicked.connect(self.get_asset)
        self.UFind.clicked.connect(self.sync_asset)

        # TODO 无法获取 thunmnail 暂时隐藏
        self.UThumbnail.hide()

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
            MMessage.warning(u'请选择一个 %s' % ("|".join([c.__name__ for c in self.class_filter])) , self)
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


def main():
    selector = USelector(class_filter=[unreal.Material])
    selector.show()


if __name__ == "__main__":
    main()
