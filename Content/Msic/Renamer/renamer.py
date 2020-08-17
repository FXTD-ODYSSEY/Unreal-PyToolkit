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

red_lib = unreal.RedArtToolkitBPLibrary()
editor_lib = unreal.EditorUtilityLibrary()
asset_lib = unreal.EditorAssetLibrary()

class AssetImportWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(AssetImportWidget, self).__init__(parent)
        DIR, file_name = os.path.split(__file__)
        file_name = os.path.splitext(file_name)[0]
        load_ui(os.path.join(DIR, "%s.ui" % file_name), self)

        # NOTE 配置默认材质路径
        self.settings = QtCore.QSettings(
            "%s.ini" % self.__class__.__name__, QtCore.QSettings.IniFormat)
        material_path = self.settings.value("material_path")
        material_path = material_path if material_path else "/Game/ArtResources/Effects/Mesh/Mat_MeshDefault.Mat_MeshDefault"
        self.Selector_LE.setText(material_path)
        self.check_material_path()

        self.Normal_BTN.clicked.connect(self.normal_settings)
        self.VTX_Anim_BTN.clicked.connect(self.vertex_anim_setting)
        self.Selector_BTN.clicked.connect(self.select_material)

        self.Help_Action.triggered.connect(lambda: webbrowser.open_new_tab(
            'http://redarttoolkit.pages.oa.com/docs/posts/cbaaea9f.html'))

    def select_material(self):
        editor_lib = unreal.EditorUtilityLibrary()
        assets = editor_lib.get_selected_assets()
        for asset in assets:
            if isinstance(asset, unreal.MaterialInterface):
                path = asset.get_path_name()
                self.Selector_LE.setText(path)
                return self.settings.setValue("material_path", path)

    def check_material_path(self,):
        material_path = self.Selector_LE.text()
        if not asset_lib.does_asset_exist(material_path):
            self.Selector_LE.clear()
            msg = u"Material 资源路径不存在"
            toast(msg)
        return material_path

    def normal_settings(self):
        material_path = self.check_material_path()
        if not material_path:
            return
        assets = editor_lib.get_selected_assets()
        for asset in assets:
            if isinstance(asset, unreal.Texture2D):
                asset.set_editor_property('srgb', False)
                TMGS_NO_MIPMAPS = unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS
                asset.set_editor_property('mip_gen_settings', TMGS_NO_MIPMAPS)
                TEXTUREGROUP_UI = unreal.TextureGroup.TEXTUREGROUP_UI
                asset.set_editor_property('lod_group', TEXTUREGROUP_UI)
            elif isinstance(asset, unreal.StaticMesh):
                material = unreal.load_asset(material_path)
                asset.set_material(0, material)
                red_lib.static_mesh_editor_refresh()
        toast(u"资源配置成功","info")

    def vertex_anim_setting(self):
        material_path = self.check_material_path()
        if not material_path:
            return
        assets = editor_lib.get_selected_assets()
        for asset in assets:
            if isinstance(asset, unreal.Texture2D):
                TF_NEAREST = unreal.TextureFilter.TF_NEAREST
                asset.set_editor_property('filter', TF_NEAREST)
                TEXTUREGROUP_UI = unreal.TextureGroup.TEXTUREGROUP_UI
                asset.set_editor_property('lod_group', TEXTUREGROUP_UI)
            elif isinstance(asset, unreal.StaticMesh):
                material = unreal.load_asset(material_path)
                asset.set_material(0, material)
                red_lib.static_mesh_use_full_precision_uv(asset, 0, True)
                red_lib.static_mesh_distance_field_resolution(asset, 0)
                red_lib.static_mesh_editor_refresh()
        toast(u"资源配置成功","info")


@error_log
def main():
    widget = AssetImportWidget()
    widget.show()


if __name__ == "__main__":
    main()
