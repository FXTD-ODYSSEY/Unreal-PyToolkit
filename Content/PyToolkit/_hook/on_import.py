# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2021-08-18 22:46:37"


import unreal


# @unreal.uclass()
# class OnAssetImport(unreal.EditorUtilityObject):
#     @unreal.ufunction(
#         static=True,
#         params=[unreal.Factory, unreal.Object],
#         meta=dict(BlurpintEvent=True),
#     )
#     def import_log(factory, created_object):
#         msg = "Import Hook Trigger"
#         unreal.SystemLibrary.print_string(None, msg, text_color=[255, 255, 255, 255])
#         print(factory, created_object)
        
def import_log(factory, created_object):
    msg = "Import Hook Trigger"
    unreal.SystemLibrary.print_string(None, msg, text_color=[255, 255, 255, 255])
    print(factory, created_object)


def main():
    import_subsystem = unreal.get_editor_subsystem(unreal.ImportSubsystem)
    global on_asset_post_import_delegate
    on_asset_post_import_delegate = unreal.OnAssetPostImport_Dyn()
    # on_asset_post_import_delegate.add_callable(OnAssetImport.import_log)
    on_asset_post_import_delegate.add_callable(import_log)
    import_subsystem.set_editor_property("on_asset_post_import",on_asset_post_import_delegate)
    print(on_asset_post_import_delegate)

if __name__ == "__main__":
    main()
