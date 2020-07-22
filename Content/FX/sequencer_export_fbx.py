# -*- coding: utf-8 -*-
"""
导出 Sequencer 选择的元素动画
使用 FBX SDK 转换为骨骼蒙皮动画
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-06-28 21:17:21'


import os
import sys
import tempfile
import itertools
import subprocess

import unreal
import fbx
import FbxCommon
from Qt import QtCore, QtWidgets, QtGui
from dayu_widgets import dayu_theme

DIR = os.path.dirname(__file__)

def alert(msg=u"msg", title=u"警告",icon=QtWidgets.QMessageBox.Warning,button_text=u"确定"):
    # NOTE 生成 Qt 警告窗口
    msg_box = QtWidgets.QMessageBox()
    msg_box.setIcon(icon)
    msg_box.setWindowTitle(title)
    msg_box.setText(msg)
    msg_box.addButton(button_text, QtWidgets.QMessageBox.AcceptRole)
    dayu_theme.apply(msg_box)
    msg_box.exec_()

def unreal_export_fbx(fbx_file):
    # NOTE 获取当前 Sequencer 中的 LevelSequence
    sequence = unreal.PyToolkitBPLibrary.get_focus_sequence()
    if not sequence:
        msg = u"请打开定序器"
        alert(msg)
        raise RuntimeError(msg)

    # NOTE 获取当前 Sequencer 中选中的 Bindings
    id_list = unreal.PyToolkitBPLibrary.get_focus_bindings(sequence)
    bindings_list = [binding for binding in sequence.get_bindings() if binding.get_id() in id_list]

    if bindings_list:
        option = unreal.FbxExportOption()
        option.set_editor_property("collision",False)
        world = unreal.EditorLevelLibrary.get_editor_world()
        unreal.SequencerTools.export_fbx(world,sequence,bindings_list,option,fbx_file)
    else:
        # NOTE 生成 Qt 警告窗口
        msg = u"请选择定序器的元素进行 FBX 导出"
        alert(msg)
        raise RuntimeError(msg)

def CreateSkeleton(lSdkManager, pName):
    # Create skeleton root
    lRootName = pName + "Root"
    lSkeletonRootAttribute = fbx.FbxSkeleton.Create(lSdkManager, lRootName)
    lSkeletonRootAttribute.SetSkeletonType(fbx.FbxSkeleton.eRoot)
    lSkeletonRoot = fbx.FbxNode.Create(lSdkManager, lRootName)
    lSkeletonRoot.SetNodeAttribute(lSkeletonRootAttribute)    
    lSkeletonRoot.LclTranslation.Set(fbx.FbxDouble3(0.0, 0.0, 0.0))
    
    # Create skeleton first limb node.
    lLimbNodeName1 = pName + "Target"
    lSkeletonLimbNodeAttribute1 = fbx.FbxSkeleton.Create(lSdkManager, lLimbNodeName1)
    lSkeletonLimbNodeAttribute1.SetSkeletonType(fbx.FbxSkeleton.eLimbNode)
    # lSkeletonLimbNodeAttribute1.Size.Set(1.0)
    lSkeletonLimbNode1 = fbx.FbxNode.Create(lSdkManager, lLimbNodeName1)
    lSkeletonLimbNode1.SetNodeAttribute(lSkeletonLimbNodeAttribute1)    
    lSkeletonLimbNode1.LclTranslation.Set(fbx.FbxDouble3(0.0, 0.0, 0.0))
    
    # Build skeleton node hierarchy. 
    lSkeletonRoot.AddChild(lSkeletonLimbNode1)
    return lSkeletonRoot

def CreateTriangle(pSdkManager, pName):
    lMesh = fbx.FbxMesh.Create(pSdkManager, pName)

    # The three vertices
    lControlPoint0 = fbx.FbxVector4(0.1, 0, 0)
    lControlPoint1 = fbx.FbxVector4(0, 0.1, 0)
    lControlPoint2 = fbx.FbxVector4(0, 0, 0.1)

    # Create control points.
    lMesh.InitControlPoints(3)
    lMesh.SetControlPointAt(lControlPoint0, 0)
    lMesh.SetControlPointAt(lControlPoint1, 1)
    lMesh.SetControlPointAt(lControlPoint2, 2)

    # Create the triangle's polygon
    lMesh.BeginPolygon()
    lMesh.AddPolygon(0) # Control point 0
    lMesh.AddPolygon(1) # Control point 1
    lMesh.AddPolygon(2) # Control point 2
    lMesh.EndPolygon()

    lNode = fbx.FbxNode.Create(pSdkManager,pName)
    lNode.SetNodeAttribute(lMesh)

    return lNode

def LinkMeshToSkeleton(pSdkManager, pPatchNode, pSkeletonRoot):
    lLimbNode1 = pSkeletonRoot.GetChild(0)
    
    # Bottom section of cylinder is clustered to skeleton root.
    lClusterToRoot = fbx.FbxCluster.Create(pSdkManager, "")
    lClusterToRoot.SetLink(pSkeletonRoot)
    lClusterToRoot.SetLinkMode(fbx.FbxCluster.eTotalOne)
    for i in range(3):
        lClusterToRoot.AddControlPointIndex(i, 1)
        
    # Center section of cylinder is clustered to skeleton limb node.
    lClusterToLimbNode1 = fbx.FbxCluster.Create(pSdkManager, "")
    lClusterToLimbNode1.SetLink(lLimbNode1)
    lClusterToLimbNode1.SetLinkMode(fbx.FbxCluster.eTotalOne)
        
    # Now we have the Patch and the skeleton correctly positioned,
    # set the Transform and TransformLink matrix accordingly.
    lXMatrix = fbx.FbxAMatrix()
    lScene = pPatchNode.GetScene()
    if lScene:
        lXMatrix = lScene.GetAnimationEvaluator().GetNodeGlobalTransform(pPatchNode)
    lClusterToRoot.SetTransformMatrix(lXMatrix)
    lClusterToLimbNode1.SetTransformMatrix(lXMatrix)
    lScene = pSkeletonRoot.GetScene()
    if lScene:
        lXMatrix = lScene.GetAnimationEvaluator().GetNodeGlobalTransform(pSkeletonRoot)
    lClusterToRoot.SetTransformLinkMatrix(lXMatrix)
    lScene = lLimbNode1.GetScene()
    if lScene:
        lXMatrix = lScene.GetAnimationEvaluator().GetNodeGlobalTransform(lLimbNode1)
    lClusterToLimbNode1.SetTransformLinkMatrix(lXMatrix)

    
    # Add the clusters to the patch by creating a skin and adding those clusters to that skin.
    # After add that skin.
    lSkin = fbx.FbxSkin.Create(pSdkManager, "")
    lSkin.AddCluster(lClusterToRoot)
    lSkin.AddCluster(lClusterToLimbNode1)
    pPatchNode.GetNodeAttribute().AddDeformer(lSkin)

def AddNodeRecursively(pNodeArray, pNode):
    if pNode:
        AddNodeRecursively(pNodeArray, pNode.GetParent())
        found = False 
        for node in pNodeArray:
            if node.GetName() == pNode.GetName():
                found = True
        if not found:
            # Node not in the list, add it
            pNodeArray += [pNode]
    
def StoreBindPose(pSdkManager, pScene, pPatchNode):
    lClusteredFbxNodes = []
    if pPatchNode and pPatchNode.GetNodeAttribute():
        lSkinCount = 0
        lClusterCount = 0
        lNodeAttributeType = pPatchNode.GetNodeAttribute().GetAttributeType()
        if lNodeAttributeType in (fbx.FbxNodeAttribute.eMesh, fbx.FbxNodeAttribute.eNurbs, fbx.FbxNodeAttribute.ePatch):
            lSkinCount = pPatchNode.GetNodeAttribute().GetDeformerCount(fbx.FbxDeformer.eSkin)
            for i in range(lSkinCount):
                lSkin = pPatchNode.GetNodeAttribute().GetDeformer(i, fbx.FbxDeformer.eSkin)
                lClusterCount += lSkin.GetClusterCount()
                
        # If we found some clusters we must add the node
        if lClusterCount:
            # Again, go through all the skins get each cluster link and add them
            for i in range(lSkinCount):
                lSkin = pPatchNode.GetNodeAttribute().GetDeformer(i, fbx.FbxDeformer.eSkin)
                lClusterCount = lSkin.GetClusterCount()
                for j in range(lClusterCount):
                    lClusterNode = lSkin.GetCluster(j).GetLink()
                    AddNodeRecursively(lClusteredFbxNodes, lClusterNode)
                    
            # Add the patch to the pose
            lClusteredFbxNodes += [pPatchNode]
            
    # Now create a bind pose with the link list
    if len(lClusteredFbxNodes):
        # A pose must be named. Arbitrarily use the name of the patch node.
        lPose = fbx.FbxPose.Create(pSdkManager, pPatchNode.GetName())
        lPose.SetIsBindPose(True)

        for lFbxNode in lClusteredFbxNodes:
            lBindMatrix = fbx.FbxAMatrix()
            lScene = lFbxNode.GetScene()
            if lScene:
                lBindMatrix = lScene.GetAnimationEvaluator().GetNodeGlobalTransform(lFbxNode)
            lPose.Add(lFbxNode, fbx.FbxMatrix(lBindMatrix))

        # Add the pose to the scene
        pScene.AddPose(lPose)

def handle_fbx(fbx_file,output_file):

    manager, scene = FbxCommon.InitializeSdkObjects()
    s = manager.GetIOSettings()
    s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Material", False)
    s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Texture", False)
    s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Audio", False)
    s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Audio", False)
    s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Shape", False)
    s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Link", False)
    s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Gobo", False)
    s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Animation", True)
    s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Character", False)
    s.SetBoolProp("Import|AdvOptGrp|FileFormat|Fbx|Global_Settings", True)
    manager.SetIOSettings(s)

    result = FbxCommon.LoadScene(manager, scene, fbx_file)
    if not result:
        raise RuntimeError("%s load Fail" % fbx_file)
    
    root = scene.GetRootNode()
    remove_list = [root.GetChild(i) for i in range(root.GetChildCount())]
    
    # NOTE 创建骨架
    root_skeleton = CreateSkeleton(manager, "Skeleton")
    target_skeleton = root_skeleton.GetChild(0)
    
    # NOTE 创建三角形
    mesh = CreateTriangle(manager, "Mesh")

    # NOTE 处理蒙皮
    LinkMeshToSkeleton(manager, mesh, root_skeleton)
    StoreBindPose(manager, scene, mesh)

    # NOTE 获取默认的动画节点
    # for i in range(scene.GetSrcObjectCount(fbx.FbxCriteria.ObjectType(fbx.FbxAnimStack.ClassId))):
    #     lAnimStack = scene.GetSrcObject(fbx.FbxCriteria.ObjectType(fbx.FbxAnimStack.ClassId), i)
    #     for j in range(lAnimStack.GetMemberCount()):
    #         anim_layer = lAnimStack.GetMember(j)

    anim_stack = scene.GetSrcObject(fbx.FbxCriteria.ObjectType(fbx.FbxAnimStack.ClassId), 0)
    anim_layer = anim_stack.GetMember(0)

    # NOTE 复制动画曲线
    for child in remove_list:
        # print(child)
        # if child.GetName() == "Transform":
        method_list = ["LclTranslation","LclRotation","LclScaling"]
        axis_list = "XYZ"
        for method,axis in itertools.product(method_list,axis_list):
            curve = getattr(child,method).GetCurve(anim_layer, axis, False)
            if curve:
                target_curve = getattr(target_skeleton,method).GetCurve(anim_layer, axis, True)
                target_curve.CopyFrom(curve)

        # NOTE 清理原始的 Transform 节点
        root.RemoveChild(child)
    
    root.AddChild(mesh)
    root.AddChild(root_skeleton)
    FbxCommon.SaveScene(manager, scene, output_file)
    manager.Destroy()
    
def main():
    temp_folder = os.path.join(tempfile.gettempdir(),"unreal_fbx")
    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)
    fbx_file = os.path.join(temp_folder,"unreal_temp.fbx")
    # output_file = os.path.join(temp_folder,"unreal_temp2.fbx")
    unreal_export_fbx(fbx_file)
    handle_fbx(fbx_file,fbx_file)
    COMMAND = 'explorer /select,"%s"' % fbx_file.replace("/","\\")
    subprocess.call(COMMAND, creationflags=0x08000000)

if __name__ == "__main__":
    main()