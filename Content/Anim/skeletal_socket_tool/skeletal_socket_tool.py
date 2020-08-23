# -*- coding: utf-8 -*-
"""
批量生成
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-07-20 19:44:01'

import os
import csv
import webbrowser
import subprocess
import unreal
from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import load_ui,QFileDialog
from codecs import open

from dayu_widgets.item_model import MTableModel, MSortFilterModel
# from dayu_widgets.message import MMessage
# from dayu_widgets import dayu_theme

from ue_util import alert

class SocketTool(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SocketTool, self).__init__(parent=parent)
        ui_file = os.path.join(__file__,"..","skeletal_socket_tool.ui")
        load_ui(ui_file,self)

        self.model = MTableModel()
        header_list = [u"骨骼",u"插槽"]
        self.header_list = [{
                            'label': data,
                            'key': data,
                            'editable': True,
                            'selectable': True,
                            'width': 400,
                        } for data in header_list]
        self.model.set_header_list(self.header_list)
        
        self.model_sort = MSortFilterModel()
        self.model_sort.setSourceModel(self.model)

        self.Table_View.setShowGrid(True)
        self.Table_View.setModel(self.model_sort)
        header = self.Table_View.horizontalHeader()
        header.setStretchLastSection(True)

        self.popMenu = QtWidgets.QMenu(self)
        action = QtWidgets.QAction(u'删除选择', self)
        action.triggered.connect(self.remove_line)
        self.popMenu.addAction(action)
        action = QtWidgets.QAction(u'添加一行', self)
        action.triggered.connect(self.add_line)
        self.popMenu.addAction(action)

        self.Table_View.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.Table_View.customContextMenuRequested.connect(self.on_context_menu)

        self.Close_Action.triggered.connect(self.close)
        self.Export_CSV_Action.triggered.connect(self.export_csv)
        self.Import_CSV_Action.triggered.connect(self.import_csv)
        self.Help_Action.triggered.connect(lambda:webbrowser.open_new_tab('http://wiki.l0v0.com/PyToolkit/#/2_skeletal_socket_tool'))
        self.Socket_BTN.clicked.connect(self.add_socket)
        self.Clear_BTN.clicked.connect(self.clear_socket)

        # NOTE 读取 csv
        self.settings = QtCore.QSettings("%s.ini" % self.__class__.__name__, QtCore.QSettings.IniFormat)
        csv_file = self.settings.value("csv_file")
        # csv_file = os.path.join(__file__,"..","test.csv")
        if csv_file and os.path.exists(csv_file):
            self.handle_csv(csv_file)

    def get_data_list(self):
        row_count = self.model.rowCount()
        column_count = self.model.columnCount()
        return [{self.header_list[j]['key']:self.model.itemData(self.model.index(i,j))[0] for j in range(column_count)} for i in range(row_count)]
    
    def remove_line(self):
        
        data_list = self.get_data_list()
        indexes = self.Table_View.selectionModel().selectedRows()
        for index in sorted(indexes,reverse=True):
            data_list.pop(index.row())
        self.model.set_data_list(data_list)

    def add_line(self):
        data_list = self.get_data_list()
        column_count = self.model.columnCount()
        data_list.append({self.header_list[j]['key']:'' for j in range(column_count)})
        self.model.set_data_list(data_list)

    def on_context_menu(self,point):
        x = point.x()
        y = point.y()
        self.popMenu.exec_(self.Table_View.mapToGlobal(QtCore.QPoint(x,y+35)))    

    def import_csv(self,path=None):
        if not path:
            path,_ = QFileDialog.getOpenFileName(self, caption=u"获取设置",filter= u"csv (*.csv)")
        # NOTE 如果文件不存在则返回空
        if not path or not os.path.exists(path):return

        self.handle_csv(path)
        self.settings.setValue("csv_file",path)

    def export_csv(self,path=None):
        if not path:
            path,_ = QFileDialog.getSaveFileName(self, caption=u"输出设置",filter= u"csv (*.csv)")
            if not path:return

        csv = ""
        row_count = self.model.rowCount()
        column_count = self.model.columnCount()
        for i in range(row_count):
            col_list = [self.model.itemData(self.model.index(i,j))[0] for j in range(column_count)]
            csv += ",".join(col_list) + "\n"

        with open(path,'w',encoding='gbk') as f:
            f.write(csv)

        # NOTE 打开输出的路径
        subprocess.Popen(['start','',os.path.dirname(path)],creationflags=0x08000000,shell=True)

    def handle_csv(self,csv_path):
        data_list = []
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            for i,row in enumerate(reader):
                data_list.append({self.header_list[j]['key']:r.decode("gbk") for j,r in enumerate(row)})
        self.model.set_data_list(data_list)
        self.Table_View.resizeColumnToContents(1)

    def get_selectal_mesh(self):
        skel_mesh_list = [a for a in unreal.EditorUtilityLibrary.get_selected_assets() if isinstance(a,unreal.SkeletalMesh)]
        if not skel_mesh_list:
            msg = u'请选择一个 Skeletal Mesh 物体'
            alert(msg)
            raise RuntimeError(msg)
        return skel_mesh_list

    def clear_socket(self):
        for skel_mesh in self.get_selectal_mesh():
            skeleton = skel_mesh.get_editor_property("skeleton")
            # NOTE 删除所有的 socket 
            socket_list = [skel_mesh.get_socket_by_index(i) for i in range(skel_mesh.num_sockets())]
            unreal.RedArtToolkitBPLibrary.delete_skeletal_mesh_socket(skeleton,socket_list)

    def add_socket(self):

        # NOTE 读取 Table View
        row_count = self.model.rowCount()
        itemData = self.model.itemData
        index = self.model.index
        data_dict = {itemData(index(i,0))[0]:itemData(index(i,1))[0] for i in range(row_count)}

        if not data_dict:
            msg = u'当前配置数据为空请导入一个 CSV'
            alert(msg)
            return

        fail_list = {}
        add_socket = unreal.RedArtToolkitBPLibrary.add_skeletal_mesh_socket
        bone_num = unreal.RedArtToolkitBPLibrary.get_skeleton_bone_num
        bone_name = unreal.RedArtToolkitBPLibrary.get_skeleton_bone_name
        for skel_mesh in self.get_selectal_mesh():
            
            skeleton = skel_mesh.get_editor_property("skeleton")
            bone_list = [bone_name(skeleton,i) for i in range(bone_num(skeleton))]

            for bone,socket in data_dict.items():
                # NOTE 检查骨骼名称是否存在
                if not socket or skel_mesh.find_socket(socket):
                    continue
                elif bone not in bone_list:
                    skel_name = skel_mesh.get_name()
                    if skel_name not in fail_list:
                        fail_list[skel_name] = []
                    fail_list[skel_name].append(bone)
                    continue

                _socket = add_socket(skeleton,bone).socket_name
                if _socket != socket:
                    skel_mesh.rename_socket(_socket,socket)

        if fail_list:
            msg = u"以下骨骼名称没有在选中的角色找到↓↓↓\n\n"
            for skel_name,bone_list in fail_list.items():
                msg += u"%s:\n%s" % (skel_name,"\n".join(bone_list))
                
            alert(msg)

def main():
    widget = SocketTool()
    widget.show()

if __name__ == "__main__":
    main()
