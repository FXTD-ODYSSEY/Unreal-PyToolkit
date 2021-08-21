# -*- coding: utf-8 -*-
"""
自动重启引擎
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2020-09-18 15:53:10"

import sys
import subprocess
import unreal
from ue_util import error_log, toast


editor_util = unreal.EditorLoadingAndSavingUtils()
sys_lib = unreal.SystemLibrary()
paths = unreal.Paths()


@error_log
def main():
    # NOTE 保存对象
    check = editor_util.save_dirty_packages_with_dialog(True, True)
    if not check:
        toast(u"保存失败")
        return

    uproject = paths.get_project_file_path()
    editor = sys.executable

    # NOTE 启动当前引擎
    subprocess.Popen([editor, uproject, "-skipcompile"], shell=True)

    # NOTE 退出引擎
    sys_lib.quit_editor()


if __name__ == "__main__":
    main()
