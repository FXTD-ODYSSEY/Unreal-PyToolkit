# -*- coding: utf-8 -*-
"""
Class Set for ToolMenuEntryScript Object
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2021-06-18 15:27:56'

import unreal
util_lib = unreal.EditorUtilityLibrary

@unreal.uclass()
class TextureReimport(unreal.ToolMenuEntryScript):
    
    @unreal.ufunction(override=True)
    def is_visible(self,context):
        # print(self.label)
        types = (unreal.Texture,)
        assets = [asset for asset in util_lib.get_selected_assets() if isinstance(asset,types)]
        return bool(assets)
    
    @unreal.ufunction(override=True)
    def get_tool_tip(self,context):
        return u'重导贴图并且按照规范压缩图片大小'
    
    
@unreal.uclass()
class UVCapture(unreal.ToolMenuEntryScript):
    
    @unreal.ufunction(override=True)
    def is_visible(self,context):
        print(self.label)
        types = (unreal.StaticMesh,unreal.SkeletalMesh)
        assets = [asset for asset in util_lib.get_selected_assets() if isinstance(asset,types)]
        return bool(assets)
    
    @unreal.ufunction(override=True)
    def get_tool_tip(self,context):
        return u'输出模型 UV 边界图'
    
    
