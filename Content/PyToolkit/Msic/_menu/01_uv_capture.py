# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2021-08-18 17:16:54"

import os
import unreal
from functools import partial
from Qt import QtCore
from ue_util import toast

# NOTE Python 3 & 2 兼容
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except:
    import Tkinter as tk
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox

# NOTE 实现
root = tk.Tk()
root.withdraw()

asset_lib = unreal.EditorAssetLibrary
render_lib = unreal.RenderingLibrary
level_lib = unreal.EditorLevelLibrary
sys_lib = unreal.SystemLibrary
static_mesh_lib = unreal.EditorStaticMeshLibrary
defer = QtCore.QTimer.singleShot


def export_asset(obj, filename, exporter, options=None, prompt=False):
    task = unreal.AssetExportTask()
    task.set_editor_property("object", obj)
    task.set_editor_property("filename", filename)
    task.set_editor_property("exporter", exporter)
    task.set_editor_property("automated", True)
    task.set_editor_property("prompt", prompt)
    task.set_editor_property("options", options) if options else None

    check = unreal.Exporter.run_asset_export_task(task)
    if not check:
        msg = "导出失败 %s" % filename
        messagebox.showwarning(u"警告", msg)
        return


def get_static_materials(mesh):
    return [
        mesh.get_material(i) for i in range(static_mesh_lib.get_number_materials(mesh))
    ]


def get_skeletal_materials(mesh):
    return [
        m.get_editor_property("material_interface")
        for m in mesh.get_editor_property("materials")
    ]


BP = unreal.load_asset("/PyToolkit/Resources/UVCapture/BP_UVCapture.BP_UVCapture")
RT = unreal.load_asset("/PyToolkit/Resources/UVCapture/RT_UV.RT_UV")
UV_MAT = unreal.load_asset("/PyToolkit/Resources/UVCapture/M_UVCapture.M_UVCapture")
delay_time = 1000


class UVCapturer(object):

    export_dir = ""
    texture_list = []
    @classmethod
    def on_capture_finish(cls, mesh, capture_actor):
        # NOTE 生成 2D 贴图
        name = os.path.basename(mesh.get_outer().get_name())
        texture = render_lib.render_target_create_static_texture2d_editor_only(RT, name)

        # NOTE 导出图片
        exporter = unreal.TextureExporterTGA()
        output_path = os.path.join(cls.export_dir, "%s.tga" % name)
        export_asset(texture, output_path, exporter)
        capture_actor.destroy_actor()
        asset_lib.delete_asset(texture.get_path_name())

    @classmethod
    def capture(cls, mesh):
        capture_actor = level_lib.spawn_actor_from_object(BP, unreal.Vector())
        capture_comp = capture_actor.get_editor_property("capture")

        if isinstance(mesh, unreal.StaticMesh):
            static_comp = capture_actor.get_editor_property("static")
            static_comp.set_editor_property("static_mesh", mesh)
            materials = get_static_materials(mesh)
            comp = capture_actor.get_editor_property("static")
        elif isinstance(mesh, unreal.SkeletalMesh):
            skeletal_comp = capture_actor.get_editor_property("skeletal")
            skeletal_comp.set_editor_property("skeletal_mesh", mesh)
            materials = get_skeletal_materials(mesh)
            # NOTE 重新获取才可以设置 override_materials
            comp = capture_actor.get_editor_property("skeletal")

        override_materials = [UV_MAT] * len(materials)
        comp.set_editor_property("override_materials", override_materials)

        capture_comp.capture_scene()
        capture_comp.capture_scene()
        # NOTE 等待资源更新
        defer(delay_time / 2, partial(cls.on_capture_finish, mesh, capture_actor))

    @classmethod
    def on_finished(cls,vis_dict):
        asset_lib.delete_loaded_assets(cls.texture_list)

        # NOTE 删除蓝图 & 恢复场景的显示
        for actor, vis in vis_dict.items():
            actor.set_is_temporarily_hidden_in_editor(vis)
            
        # NOTE 打开输出路径
        os.startfile(cls.export_dir)
        toast("输出成功")

    @classmethod
    def run(cls):
        types = (unreal.SkeletalMesh, unreal.StaticMesh)
        meshes = [
            a
            for a in unreal.EditorUtilityLibrary.get_selected_assets()
            if isinstance(a, types)
        ]

        # NOTE 选择输出路径
        cls.texture_list = []
        cls.export_dir = filedialog.askdirectory(title=u"选择输出的路径")
        if not cls.export_dir:
            return

        if not meshes:
            toast(u"请选择 StaticMesh 或 SkeletalMesh")
            return

        # NOTE 记录和隐藏所有 Actor 的显示
        vis_dict = {}
        for actor in level_lib.get_all_level_actors():
            vis = actor.is_temporarily_hidden_in_editor()
            vis_dict[actor] = vis
            actor.set_is_temporarily_hidden_in_editor(True)

        for i, mesh in enumerate(meshes):
            defer(delay_time * i, partial(cls.capture, mesh))
        defer(delay_time * (i + 1), partial(cls.on_finished, vis_dict))

        

if __name__ == "__main__":
    UVCapturer.run()
