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

import unreal

from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import load_ui, QFileDialog


# editor_lib = unreal.EditorLevelLibrary()
# location,rotation = editor_lib.get_level_viewport_camera_info()
# print(location)
# print(rotation)

level_lib = unreal.EditorLevelLibrary()

origin,extent,radius = unreal.EditorUtilityLibrary.get_selection_bounds()
print(extent)
path = '/Engine/BasicShapes/Cube.Cube'

asset = unreal.load_asset(path)
actor = level_lib.spawn_actor_from_object(asset,origin-extent)
# actor.set_actor_relative_scale3d(extent)


for actor in unreal.EditorLevelLibrary.get_selected_level_actors():
    # comp = actor.static_mesh_component
    # min_v,max_v = comp.get_local_bounds()
    # print(min_v)
    # print(max_v)
    min_v,max_v = actor.get_actor_bounds(True)
    print(min_v)
    print(max_v)


