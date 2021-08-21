# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2021-08-18 22:46:37'


import unreal

@unreal.uclass()
class OnAssetSaveValidator(unreal.EditorValidatorBase):
    @unreal.ufunction(override=True)
    def can_validate_asset(self,asset):
        msg = 'Save Hook Trigger'
        unreal.SystemLibrary.print_string(None,msg,text_color=[255,255,255,255])
        return super(OnAssetSaveValidator,self).can_validate_asset(asset)


def main():
    validator = OnAssetSaveValidator()
    validator.set_editor_property("is_enabled",True)
    validate_subsystem = unreal.get_editor_subsystem(unreal.EditorValidatorSubsystem)
    validate_subsystem.add_validator(validator)


if __name__ == "__main__":
    main()
