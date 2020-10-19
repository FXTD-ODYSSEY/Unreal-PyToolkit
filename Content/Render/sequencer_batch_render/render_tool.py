# -*- coding: utf-8 -*-
"""
渲染 sequencer 的画面
选择 LevelSequence 批量进行渲染

- [x] 通过 QSettings 记录
- [x] 进度条显示
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2020-07-14 21:57:32"

import unreal

import os
import re
import ast
import json
import posixpath
import subprocess
import webbrowser
from functools import partial
from collections import OrderedDict

try:
    from ConfigParser import ConfigParser
except:
    from configParser import ConfigParser

from Qt.QtCompat import loadUi
from Qt import QtCore, QtWidgets, QtGui
from UE_Util import toast, alert


sys_lib = unreal.SystemLibrary()
project_dir = sys_lib.get_project_directory()


def render(sequence_list, i, output_directory="C:/render", output_format="{sequence}"):

    # NOTE 如果超出数组则退出执行
    if i >= len(sequence_list):
        # NOTE 输出完成 打开输出文件夹的路径
        os.startfile(output_directory)
        return

    # NOTE 获取当前渲染序号下的 LevelSequence
    sequence = sequence_list[i]

    # NOTE 配置渲染参数
    settings = unreal.MovieSceneCaptureSettings()
    path = unreal.DirectoryPath(output_directory)
    settings.set_editor_property("output_directory", path)
    settings.set_editor_property("output_format", output_format)
    settings.set_editor_property("overwrite_existing", True)
    settings.set_editor_property("game_mode_override", None)
    settings.set_editor_property("use_relative_frame_numbers", False)
    settings.set_editor_property("handle_frames", 0)
    settings.set_editor_property("zero_pad_frame_numbers", 4)
    settings.set_editor_property("use_custom_frame_rate", True)
    settings.set_editor_property("custom_frame_rate", unreal.FrameRate(24, 1))

    # NOTE 渲染大小
    w, h = 1280, 720
    settings.set_editor_property("resolution", unreal.CaptureResolution(w, h))

    settings.set_editor_property("enable_texture_streaming", False)
    settings.set_editor_property("cinematic_engine_scalability", True)
    settings.set_editor_property("cinematic_mode", True)
    settings.set_editor_property("allow_movement", False)
    settings.set_editor_property("allow_turning", False)
    settings.set_editor_property("show_player", False)
    settings.set_editor_property("show_hud", False)

    # NOTE 设置默认的自动渲染参数
    option = unreal.AutomatedLevelSequenceCapture()
    option.set_editor_property("use_separate_process", False)
    option.set_editor_property("close_editor_when_capture_starts", False)
    option.set_editor_property("additional_command_line_arguments", "-NOSCREENMESSAGES")
    option.set_editor_property("inherited_command_line_arguments", "")
    option.set_editor_property("use_custom_start_frame", False)
    option.set_editor_property("use_custom_end_frame", False)
    option.set_editor_property("warm_up_frame_count", 0.0)
    option.set_editor_property("delay_before_warm_up", 0)
    option.set_editor_property("delay_before_shot_warm_up", 0.0)
    option.set_editor_property("write_edit_decision_list", True)
    # option.set_editor_property("custom_start_frame",unreal.FrameNumber(0))
    # option.set_editor_property("custom_end_frame",unreal.FrameNumber(0))

    option.set_editor_property("settings", settings)
    option.set_editor_property(
        "level_sequence_asset", unreal.SoftObjectPath(sequence.get_path_name())
    )

    # NOTE 设置自定义渲染参数
    option.set_image_capture_protocol_type(unreal.CompositionGraphCaptureProtocol)
    protocol = option.get_image_capture_protocol()
    # NOTE 这里设置 Base Color 渲染 Base Color 通道，可以根据输出的 UI 设置数组名称
    passes = unreal.CompositionGraphCapturePasses(["Base Color"])
    protocol.set_editor_property("include_render_passes", passes)
    # protocol.set_editor_property("compression_quality",100)

    # NOTE 设置全局变量才起作用！
    global on_finished_callback
    on_finished_callback = unreal.OnRenderMovieStopped(
        lambda s: render(sequence_list, i + 1, output_directory, output_format)
    )
    unreal.SequencerTools.render_movie(option, on_finished_callback)


def batch_render(output_directory="C:/render", output_format="{sequence}"):

    # NOTE 获取当前选择的 LevelSequence
    sequence_list = [
        asset
        for asset in unreal.EditorUtilityLibrary.get_selected_assets()
        if isinstance(asset, unreal.LevelSequence)
    ]

    if not sequence_list:
        toast(u"请选择一个 LevelSequence")
        return

    if not os.access(output_directory, os.W_OK):
        toast(u"当前输出路径非法")
        return
    elif not os.path.exists(output_directory):
        # NOTE 路径不存在则创建文件夹
        os.makedirs(output_directory)
    elif os.path.isfile(output_directory):
        # NOTE 如果传入文件路径则获取目录
        output_directory = os.path.dirname(output_directory)

    render(sequence_list, 0, output_directory, output_format)


HDRCaptureGamut = {
    "HCGM_ACES": unreal.HDRCaptureGamut.HCGM_ACES,
    "HCGM_ACE_SCG": unreal.HDRCaptureGamut.HCGM_ACE_SCG,
    "HCGM_LINEAR": unreal.HDRCaptureGamut.HCGM_LINEAR,
    "HCGM_P3DCI": unreal.HDRCaptureGamut.HCGM_P3DCI,
    "HCGM_REC2020": unreal.HDRCaptureGamut.HCGM_REC2020,
    "HCGM_REC709": unreal.HDRCaptureGamut.HCGM_REC709,
}

proctocol_dict = {
    0: unreal.CompositionGraphCaptureProtocol,
    1: unreal.ImageSequenceProtocol_JPG,
    2: unreal.ImageSequenceProtocol_EXR,
    3: unreal.ImageSequenceProtocol_PNG,
    4: unreal.ImageSequenceProtocol_BMP,
    5: unreal.VideoCaptureProtocol,
}


def read_json():
    DIR = os.path.dirname(os.path.abspath(__file__))
    json_path = posixpath.join(DIR, "config.json")
    with open(json_path, "r") as f:
        return json.load(f)


class SequencerRenderTool(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SequencerRenderTool, self).__init__()
        DIR = os.path.dirname(__file__)
        ui_path = os.path.join(DIR, "render_tool.ui")
        loadUi(ui_path, self)

        name = "%s.ini" % self.__class__.__name__
        self.settings = QtCore.QSettings(name, QtCore.QSettings.IniFormat)
        cb_list = self.settings.value("cb_list")
        cb_list = cb_list if isinstance(cb_list, list) else [cb_list] if cb_list else []

        self.json_config = read_json()

        self.ini_file = posixpath.join(
            project_dir,
            "Saved",
            "Config",
            "Windows",
            "EditorPerProjectUserSettings.ini",
        )
        self.ini_file = self.ini_file if os.path.exists(self.ini_file) else ""
        for cb in self.Pass_Container.findChildren(QtWidgets.QCheckBox):
            if cb.objectName() in cb_list:
                cb.setChecked(True)
            cb.clicked.connect(self.dump_settings)
            self.Select_BTN.clicked.connect(partial(cb.setChecked, True))
            self.Toggle_BTN.clicked.connect(cb.toggle)
            self.NonSelect_BTN.clicked.connect(partial(cb.setChecked, False))

        self.Select_BTN.clicked.connect(self.dump_settings)
        self.Toggle_BTN.clicked.connect(self.dump_settings)
        self.NonSelect_BTN.clicked.connect(self.dump_settings)
        self.Proctocol_Combo.currentIndexChanged.connect(self.dump_settings)
        self.Proctocol_Combo.currentIndexChanged.connect(self.combo_changed)

        self.Config_LE.setText(self.ini_file)
        self.Config_Browse_BTN.clicked.connect(self.browse_file)
        self.Browse_BTN.clicked.connect(self.browse_directory)
        self.Render_BTN.clicked.connect(self.batch_render)
        self.Locate_BTN.clicked.connect(
            lambda: os.startfile(self.Output_LE.text())
            if os.path.exists(self.Output_LE.text())
            else toast(u"输出目录的路径不存在")
        )
        self.Config_BTN.clicked.connect(self.read_config)

        self.Help_Action.triggered.connect(
            lambda: webbrowser.open_new_tab(
                "http://wiki.l0v0.com/unreal/PyToolkit/#/render/1_render_tool"
            )
        )

        self.capture_settings = unreal.MovieSceneCaptureSettings()
        self.read_config()
        index = self.settings.value("index")
        self.Proctocol_Combo.setCurrentIndex(int(index)) if index else None

    def browse_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, caption=u"获取 Unreal 用户配置文件", filter="ini (*.ini);;所有文件 (*)"
        )

        if not os.path.exists(path):
            toast(u"配置路径不存在")
            return

        self.Config_LE.setText(path)

    def browse_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self)
        self.Output_LE.setText(directory)

    def dump_settings(self):
        cb_list = [
            cb.objectName()
            for cb in self.Pass_Container.findChildren(QtWidgets.QCheckBox)
            if cb.isChecked()
        ]
        index = self.Proctocol_Combo.currentIndex()
        self.settings.setValue("cb_list", cb_list)
        self.settings.setValue("index", index)

    def read_config(self, text=True):
        self.ini_file = self.Config_LE.text()
        if not os.path.exists(self.ini_file):
            toast(u"配置路径不存在")
            self.Config_LE.setText("")
            return

        self.config = ConfigParser()
        self.config.read(self.ini_file)

        section = "MovieSceneCaptureUIInstance AutomatedLevelSequenceCapture"
        option = "Settings"
        capture_settings = self.config.get(section, option)
        capture_settings_dict = self.json_config[section][option]
        capture_settings = capture_settings[1:-1]
        pattern = re.compile("\((.+?)\)")
        value_list = []
        for i, match in enumerate(pattern.findall(capture_settings)):
            capture_settings = capture_settings.replace(match, "$$%s$$" % i)
            value_list.append(match)

        # NOTE 设置
        for pair in capture_settings.split(","):
            k, v = pair.split("=")
            v = value_list[int(v[3])] if v.startswith("($$") else v
            k = capture_settings_dict.get(k)
            if not k:
                continue
            elif k == "output_directory":
                self.Output_LE.setText(v[6:-1].replace("\\\\", "\\")) if text else None
            elif text and k == "output_format":
                self.FileName_LE.setText(v[1:-1]) if text else None
            elif k == "game_mode_override":
                if v == "None":
                    continue
                v = v.split('"')[1]
                v = unreal.load_class(None, v)
                self.capture_settings.set_editor_property(k, v)
            elif k == "custom_frame_rate":
                numerator, denominator = v.split(",")
                numerator = numerator.split("=")[1]
                denominator = denominator.split("=")[1]
                v = unreal.FrameRate(int(numerator), int(denominator))
                self.capture_settings.set_editor_property(k, v)
            elif k == "resolution":
                x, y = v.split(",")
                x = x.split("=")[1]
                y = y.split("=")[1]
                v = unreal.CaptureResolution(int(x), int(y))
                self.capture_settings.set_editor_property(k, v)
            else:
                v = ast.literal_eval(v)
                self.capture_settings.set_editor_property(k, v)

    def combo_changed(self, i):
        self.Custom_Pass_Container.setVisible(i == 0)
        self.adjustSize()

    def batch_render(self):
        # NOTE 获取当前选择的 LevelSequence
        sequence_list = [
            asset
            for asset in unreal.EditorUtilityLibrary.get_selected_assets()
            if isinstance(asset, unreal.LevelSequence)
        ]

        if not sequence_list:
            toast(u"请选择一个 \n LevelSequence")
            return

        self.ini_file = self.Config_LE.text()
        if not os.path.exists(self.ini_file):
            toast(u"配置路径不存在")
            self.Config_LE.setText("")
            return

        self.output_directory = self.Output_LE.text()
        if not os.access(self.output_directory, os.W_OK):
            toast(u"当前输出路径非法")
            return
        elif not os.path.exists(self.output_directory):
            # NOTE 路径不存在则创建文件夹
            os.makedirs(self.output_directory)
        elif os.path.isfile(self.output_directory):
            # NOTE 如果传入文件路径则获取目录
            self.output_directory = os.path.dirname(self.output_directory)

        self.render(sequence_list, 0)

    def setup_capture(self):
        self.read_config(False)
        path = unreal.DirectoryPath(self.output_directory)
        self.capture_settings.set_editor_property("output_directory", path)
        self.capture_settings.set_editor_property(
            "output_format", self.FileName_LE.text()
        )

        index = self.Proctocol_Combo.currentIndex()
        protocol = proctocol_dict.get(index)

        capture = unreal.AutomatedLevelSequenceCapture()
        section = "MovieSceneCaptureUIInstance AutomatedLevelSequenceCapture"
        for option, attr in self.json_config.get(section).items():
            if not self.config.has_option(section, option):
                continue
            v = self.config.get(section, option)
            if option == "Settings":
                capture.set_editor_property("settings", self.capture_settings)
                continue
            elif attr == "custom_end_frame":
                pattern = re.compile("(\d+)")
                num = pattern.search(v).group(0)
                v = unreal.FrameNumber(int(num))
            elif attr == "custom_start_frame":
                pattern = re.compile("(\d+)")
                num = pattern.search(v).group(0)
                v = unreal.FrameNumber(int(num))
            elif attr == "audio_capture_protocol_type":
                v = unreal.SoftClassPath(v)
            elif attr == "additional_command_line_arguments":
                pass
            elif attr == "image_capture_protocol_type":
                capture.set_image_capture_protocol_type(protocol)
                protocol_name = (
                    "MovieSceneCaptureUIInstance_ImageProtocol %s" % protocol.__name__
                )
                print(protocol_name)
                protocol = capture.get_image_capture_protocol()
                for pro_name, pro_attr in self.json_config.get(
                    protocol_name, {}
                ).items():
                    if not self.config.has_option(protocol_name, pro_name):
                        continue
                    pro_v = self.config.get(protocol_name, pro_name)
                    if pro_attr == "capture_gamut":
                        pro_v = HDRCaptureGamut[pro_v.upper()]
                    elif pro_attr == "post_processing_material":
                        if pro_v == "None":
                            continue
                        pro_v = unreal.SoftObjectPath(pro_v)
                    elif pro_attr == "include_render_passes":
                        # NOTE 获取勾选的 passes
                        name_list = [
                            cb.text()
                            for cb in self.Pass_Container.findChildren(
                                QtWidgets.QCheckBox
                            )
                            if cb.isChecked()
                        ]
                        print(name_list)
                        pro_v = unreal.CompositionGraphCapturePasses(name_list)
                    else:
                        pro_v = ast.literal_eval(pro_v)
                    protocol.set_editor_property(pro_attr, pro_v)
                continue
            else:
                v = ast.literal_eval(v)
            capture.set_editor_property(attr, v)
        return capture

    def render(self, sequence_list, i):

        progress = (i / len(sequence_list)) * 100
        self.ProgressBar.setValue(progress)
        # NOTE 如果超出数组则退出执行
        if i >= len(sequence_list):
            # NOTE 输出完成 打开输出文件夹的路径
            os.startfile(self.output_directory)
            toast(u"渲染完成~", "info")
            print("渲染完成")
            return

        # NOTE 设置全局变量才起作用！
        global on_finished_callback
        sequence = sequence_list[i]
        self.capture = self.setup_capture()
        self.capture.set_editor_property(
            "level_sequence_asset", unreal.SoftObjectPath(sequence.get_path_name())
        )
        on_finished_callback = unreal.OnRenderMovieStopped(
            lambda s: self.render(sequence_list, i + 1)
        )
        unreal.SequencerTools.render_movie(self.capture, on_finished_callback)

        # # NOTE 设置过滤
        # self.PostProcessMaterial_Selector.class_filter = unreal.Material
        # self.GameMode_Selector.class_filter = unreal.GameMode

        # # NOTE 设置隐藏
        # self.Animation_Group.toggled.connect(
        #     lambda c: self.set_children_visible(self.Animation_Group, c))
        # self.Cinematic_Group.toggled.connect(
        #     lambda c: self.set_children_visible(self.Cinematic_Group, c))
        # self.Cinematic_BTN.toggled.connect(
        #     self.Cinematic_Detail_Setting.setVisible)
        # self.Cinematic_BTN.toggled.connect(
        #     lambda c: self.Cinematic_BTN.setText(u"▲" if c else u"▼"))

    # def set_children_visible(self, widget, show=True):
    #     for widget in widget.children():
    #         if widget is self.Cinematic_Detail_Setting:
    #             self.set_children_visible(widget, show)
    #         elif isinstance(widget, QtWidgets.QWidget):
    #             widget.setVisible(show)
    #             self.set_children_visible(widget, show)


def main():
    RenderUI = SequencerRenderTool()
    RenderUI.show()


if __name__ == "__main__":
    main()
    # batch_render("G:/render")
