# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2021-08-19 00:38:52'

import os
import sys
import shutil
import tempfile
import subprocess
import contextlib

import unreal

DIR = os.path.dirname(__file__)
PLUGIN = "PyToolkit"
plugins = unreal.Paths.project_plugins_dir()
bin = os.path.join(plugins, PLUGIN, "bin")
CONVERT = os.path.abspath(os.path.join(bin, "convert.exe"))

util_lib = unreal.EditorUtilityLibrary
asset_tool = unreal.AssetToolsHelpers.get_asset_tools()

# NOTE 生成导入 task
def texture_import_task(filename="", destination=""):
    task = unreal.AssetImportTask()
    task.set_editor_property("automated", True)
    task.set_editor_property("destination_path", destination)
    task.set_editor_property("filename", filename)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    return task

@contextlib.contextmanager
def copy_texture(texture_path, size):
    texture_name = os.path.basename(texture_path)
    temp_path = os.path.join(tempfile.gettempdir(), texture_name)
    # NOTE 如果 size 为 0 则原图导入
    if size:
        os.path.exists(temp_path) and os.remove(temp_path)
        shutil.copyfile(texture_path, temp_path)
        resize_texture(texture_path, size)
    yield
    if size:
        os.path.exists(texture_path) and os.remove(texture_path)
        shutil.copyfile(temp_path, texture_path)
        os.path.exists(temp_path) and os.remove(temp_path)
        
def resize_texture(texture_path, size):
    assert size != 0, "贴图大小不能为0"

    # NOTE imagmagick 调整图片尺寸
    commands = [
        '"%s"' % CONVERT,
        '"%s"' % texture_path,
        "-channel RGBA",
        "-separate",
        # "-sharpen 0:0.55",
        "-resize %sx%s" % (size, size),
        "-combine",
        '"%s"' % texture_path,
    ]
    command = " ".join(commands)
    subprocess.call(command, shell=True)
    return True


def main():
    # NOTE 获取贴图调整的大小
    size = next(iter(sys.argv[1:]), 0)
    # NOTE 判断字符串是否是数字
    size = abs(int(size)) if size.isdigit() else 0
    print(size)
    for texture in util_lib.get_selected_assets():
        if not isinstance(texture, unreal.Texture):
            continue
        data = texture.get_editor_property("asset_import_data")
        texture_path = data.get_first_filename()
        path = texture.get_outer().get_path_name()
        msg = "贴图文件不存在，请重新导入\n引擎路径: %s\n贴图路径: %s" % (path, texture_path)
        assert os.path.exists(texture_path), msg
        asset_folder, name = os.path.split(texture.get_outer().get_path_name())

        texture_path = os.path.abspath(texture_path)
        
        with copy_texture(texture_path, size):
            task = texture_import_task(texture_path, asset_folder)
            name and task.set_editor_property("destination_name", name)
            asset_tool.import_asset_tasks([task])

if __name__ == "__main__":
    main()


