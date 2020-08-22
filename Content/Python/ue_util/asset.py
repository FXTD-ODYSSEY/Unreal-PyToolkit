# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-08-09 10:43:39'

import unreal

def create_asset(asset_path='', unique_name=True, asset_class=None, asset_factory=None):
    if unique_name:
        asset_path, _ = unreal.AssetToolsHelpers.get_asset_tools(
        ).create_unique_asset_name(base_package_name=asset_path, suffix='')
    if not unreal.EditorAssetLibrary.does_asset_exist(asset_path=asset_path):
        path = asset_path.rsplit('/', 1)[0]
        name = asset_path.rsplit('/', 1)[1]
        return unreal.AssetToolsHelpers.get_asset_tools().create_asset(asset_name=name, package_path=path, asset_class=asset_class, factory=asset_factory)
    return unreal.load_asset(asset_path)