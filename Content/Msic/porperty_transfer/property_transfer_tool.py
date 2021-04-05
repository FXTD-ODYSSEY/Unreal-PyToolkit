# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2021-04-01 20:12:44'

import os
import sys
import json
from pprint import pprint
from collections import defaultdict

import unreal
from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import load_ui, QFileDialog
from ue_util import error_log, toast, create_asset, unreal_progress
from dayu_widgets.item_model import MTableModel, MSortFilterModel

material_lib = unreal.MaterialEditingLibrary()
level_lib = unreal.EditorLevelLibrary()
util_lib = unreal.EditorUtilityLibrary()
asset_lib = unreal.EditorAssetLibrary()
sys_lib = unreal.SystemLibrary()
mat_lib = unreal.MaterialEditingLibrary()
asset_tool = unreal.AssetToolsHelpers.get_asset_tools()
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
py_lib = unreal.PyToolkitBPLibrary()
DIR = os.path.dirname(__file__)

def cast(typ,obj):
    try:
        return getattr(unreal,typ).cast(obj)
    except:
        return None

def get_material_paramters(expressions):
    """
    inspire by https://github.com/20tab/UnrealEnginePython/issues/103
    """
    paramters = defaultdict(set)
    for expresion in expressions:
        func = cast("MaterialExpressionMaterialFunctionCall",expresion)
        if func:
            func = func.get_editor_property("material_function")
            expressions = py_lib.get_material_function_expressions(func)
            params = get_material_paramters(expressions)
            for group,param in params.items():
                for p in param:
                    paramters[str(group)].add(str(p))
            continue

        param = cast("MaterialExpressionParameter",expresion)
        if not param:
            param = cast("MaterialExpressionTextureSampleParameter",expresion)
        if not param:
            param = cast("MaterialExpressionFontSampleParameter",expresion)
        
        if param:
            group = param.get_editor_property("group")
            parameter_name = param.get_editor_property("parameter_name")
            # print("%s %s" % (group,parameter_name,))
            paramters[str(group)].add(str(parameter_name))
    
    return paramters

def copy_material(material):
    # print(dir(material))
    scalars = material_lib.get_scalar_parameter_names(material)
    vectors = material_lib.get_vector_parameter_names(material)
    switches = material_lib.get_static_switch_parameter_names(material)
    textures = material_lib.get_texture_parameter_names(material)
    textures = material_lib.get_texture_parameter_names(material)
    all_params = []
    all_params.extend(scalars)
    all_params.extend(vectors)
    all_params.extend(switches)
    all_params.extend(textures)
    
    parent_material = material.get_base_material()


    expressions = py_lib.get_material_expressions(parent_material)
    paramters = get_material_paramters(expressions)
    paramters = {grp:[p for p in sorted(params) if p in all_params] for grp,params in sorted(paramters.items())}
    
    
    print(json.dumps(paramters))
    
def main():
    assets = util_lib.get_selected_assets()
    

    for asset in assets:
        if isinstance(asset,unreal.MaterialInterface):
            copy_material(asset)
    
    # properties = py_lib.get_all_properties(material.get_class())
    # print(properties)


if __name__ == "__main__":
    main()
    

