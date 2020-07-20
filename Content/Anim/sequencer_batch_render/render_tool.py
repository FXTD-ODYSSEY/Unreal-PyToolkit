# -*- coding: utf-8 -*-
"""
渲染 sequencer 的画面
选择 LevelSequence 批量进行渲染
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-07-14 21:57:32'

import unreal

import os
import json
import subprocess
from functools import partial
from collections import OrderedDict

from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import loadUi
from dayu_widgets import dayu_theme

def alert(msg=u"msg", title=u"警告", button_text=u"确定"):
    # NOTE 生成 Qt 警告窗口
    msg_box = QtWidgets.QMessageBox()
    msg_box.setIcon(QtWidgets.QMessageBox.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(msg)
    msg_box.addButton(button_text, QtWidgets.QMessageBox.AcceptRole)
    unreal.parent_external_window_to_slate(msg_box.winId())
    msg_box.exec_()

def render(sequence_list,i,output_directory="C:/render",output_format="{sequence}"):
    
    # NOTE 如果超出数组则退出执行
    if i >= len(sequence_list):
        # NOTE 输出完成 打开输出文件夹的路径
        subprocess.call(["start","",output_directory], creationflags=0x08000000,shell=True)
        return

    # NOTE 获取当前渲染序号下的 LevelSequence
    sequence = sequence_list[i]

    # NOTE 配置渲染参数
    settings = unreal.MovieSceneCaptureSettings()
    path = unreal.DirectoryPath(output_directory)
    settings.set_editor_property("output_directory",path)
    settings.set_editor_property("output_format",output_format)
    settings.set_editor_property("overwrite_existing",True)
    settings.set_editor_property("game_mode_override",None)
    settings.set_editor_property("use_relative_frame_numbers",False)
    settings.set_editor_property("handle_frames",0)
    settings.set_editor_property("zero_pad_frame_numbers",4)
    settings.set_editor_property("use_custom_frame_rate",True)
    settings.set_editor_property("custom_frame_rate",unreal.FrameRate(24, 1))

    # NOTE 渲染大小
    w,h = 1280,720
    settings.set_editor_property("resolution",unreal.CaptureResolution(w,h))
    
    settings.set_editor_property("enable_texture_streaming",False)
    settings.set_editor_property("cinematic_engine_scalability",True)
    settings.set_editor_property("cinematic_mode",True)
    settings.set_editor_property("allow_movement",False)
    settings.set_editor_property("allow_turning",False)
    settings.set_editor_property("show_player",False)
    settings.set_editor_property("show_hud",False)

    # NOTE 设置默认的自动渲染参数
    option = unreal.AutomatedLevelSequenceCapture()
    option.set_editor_property("use_separate_process",False)
    option.set_editor_property("close_editor_when_capture_starts",False)
    option.set_editor_property("additional_command_line_arguments","-NOSCREENMESSAGES")
    option.set_editor_property("inherited_command_line_arguments","")
    option.set_editor_property("use_custom_start_frame",False)
    option.set_editor_property("use_custom_end_frame",False)
    option.set_editor_property("warm_up_frame_count",0.0)
    option.set_editor_property("delay_before_warm_up",0)
    option.set_editor_property("delay_before_shot_warm_up",0.0)
    option.set_editor_property("write_edit_decision_list",True)
    # option.set_editor_property("custom_start_frame",unreal.FrameNumber(0))
    # option.set_editor_property("custom_end_frame",unreal.FrameNumber(0))
        
    option.set_editor_property("settings",settings)
    option.set_editor_property("level_sequence_asset",unreal.SoftObjectPath(sequence.get_path_name()))

    # NOTE 设置自定义渲染参数
    option.set_image_capture_protocol_type(unreal.CompositionGraphCaptureProtocol)
    protocol = option.get_image_capture_protocol()
    # NOTE 这里设置 Base Color 渲染 Base Color 通道，可以根据输出的 UI 设置数组名称
    passes = unreal.CompositionGraphCapturePasses(["Base Color"])
    protocol.set_editor_property("include_render_passes",passes)
    # protocol.set_editor_property("compression_quality",100)

    # NOTE 设置全局变量才起作用！
    global on_finished_callback
    on_finished_callback = unreal.OnRenderMovieStopped(
        lambda s:render(sequence_list,i+1,output_directory,output_format))
    unreal.SequencerTools.render_movie(option,on_finished_callback)
    

def batch_render(output_directory="C:/render",output_format="{sequence}"):

    
    # NOTE 获取当前选择的 LevelSequence
    sequence_list = [asset for asset in unreal.EditorUtilityLibrary.get_selected_assets() if isinstance(asset,unreal.LevelSequence)]

    if not sequence_list:
        alert(u"请选择一个 LevelSequence")
        return

    if not os.access(output_directory, os.W_OK):
        alert(u"当前输出路径非法")
        return
    elif os.path.exists(output_directory):
        # NOTE 路径不存在则创建文件夹
        os.makedirs(output_directory)
    elif os.path.isfile(output_directory):
        # NOTE 如果传入文件路径则获取目录
        output_directory = os.path.dirname(output_directory)

    render(sequence_list,0,output_directory,output_format)

def ui_PyInit(widget):
    if not hasattr(widget,"children"):
        return

    # NOTE 初始化 PyInit 中配置的方法
    data = widget.property("PyInit")
    if data:
        try:
            data = json.loads(data,object_pairs_hook=OrderedDict)
            for method,param in data['method'].items():
                param = param if isinstance(param,list) else [param]
                getattr(widget,method)(*param)
        except:
            pass

    for child in widget.children():
        ui_PyInit(child)


class RenderWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(RenderWidget, self).__init__()
        DIR = os.path.dirname(__file__)
        ui_path = os.path.join(DIR,"render_tool.ui")
        loadUi(ui_path,self)
        # NOTE 初始化配置方法
        ui_PyInit(self)

def main():
    widget = RenderWidget()
    widget.show()

if __name__ == "__main__":
    main()
    
