import os

import maya.api.OpenMaya as om
import maya.cmds as cmds

from ...core import data_utils as dutil
from . import shapes as shp

# maya modules dependent functions

def setIKFKSwitch(jntConstraintSelection:list, switchControl, 
                  fkControls:list|None=None, ikControls:list|None=None):
    ''' Sets up IK/FK joints and/or controllers switch configuration from the joint constraint selection to the provided switch control. '''
    for jntConstraint in jntConstraintSelection:
        if cmds.nodeType(jntConstraint) == 'parentConstraint':
            print(jntConstraint)
            attrs=cmds.attributeInfo(jntConstraint, all=True)
            attrs.reverse()
            for attr in attrs:
                if 'ik' in attr.lower():
                    cmds.select(switchControl)
                    if 'ik' not in cmds.attributeInfo(switchControl, all=True):
                        cmds.addAttr(shortName='ik', defaultValue=0, minValue=0, maxValue=1, attributeType="short", k=True)
                    cmds.connectAttr(f'{switchControl}.ik', f'{jntConstraint}.{attr}')
                    cmds.select(cl=True)
                    break
            for attr in attrs:
                if 'fk' in attr.lower():
                    cmds.select(switchControl)
                    if 'fk' not in cmds.attributeInfo(switchControl, all=True):
                        cmds.addAttr(shortName='fk', defaultValue=1, minValue=0, maxValue=1, attributeType="short")
                    cmds.connectAttr(f'{switchControl}.fk', f'{jntConstraint}.{attr}')
                    cmds.select(cl=True)
                    break
    cmds.expression(s=f'{switchControl}.fk = 1 - {switchControl}.ik', name='ikSwitch')

    if fkControls:
        for ctrl in fkControls:
            cmds.connectAttr(f'{switchControl}.fk', f'{ctrl}.visibility')
    if ikControls:
        for ctrl in ikControls:
            cmds.connectAttr(f'{switchControl}.ik', f'{ctrl}.visibility')

def createIKHandle(handleName:str, jointStart, jointEnd, poleTarget=None, 
                   ikCtrl=None, colorIndex:int=6, jntNameStr='jnt', distance=10, ctrlSize=4, 
                   shapeDirectory=None):
    ''' 
    Sets up standard IkHandle configuration with an optional pole vector control.
    Pole Vector control is placed based on the first (jointStart), mid (poleTarget), and end (jointEnd) joints for exact precision.
    Shape Directory required for pole vector control shape, must include 'shapes_cv.json' file with the desired shape data.
    '''
    if cmds.objectType(jointStart) != 'joint' or cmds.objectType(jointEnd) != 'joint':
        return None

    cmds.ikHandle(startJoint=jointStart, endEffector=jointEnd, name=handleName)
    cmds.select(clear=True)
    cmds.orientConstraint(handleName, jointEnd)
    ikEffector=cmds.listRelatives(jointEnd, type='ikEffector')
    if ikEffector:
        cmds.rename(ikEffector, handleName+'_effector')
    if ikCtrl:
        cmds.parent(handleName, ikCtrl)

    if poleTarget and cmds.objectType(poleTarget) == 'joint':
        if not shapeDirectory:
             shapeDirectory=os.path.join(cmds.pluginInfo('creativeSkeletons.py', query=True, path=True).strip('.py'), 
                                         'creativeLibrary', 'data')
        shapeData=dutil.load_data(shapeDirectory, 'shapes_cv.json')

        if jntNameStr in poleTarget:
            ctrlName=poleTarget.replace(jntNameStr, 'ctrl')
        else:
            ctrlName=poleTarget+'_ctrl'

        overrideColor=cmds.colorIndex(colorIndex, q=True)
        ctrl=shp.customShape(shapeData, 'sphere', name=ctrlName, typeOverride=overrideColor, radius=ctrlSize)

        startVector=om.MVector(cmds.xform(jointStart, query=True, ws=True, t=True))
        endVector=om.MVector(cmds.xform(jointEnd, query=True, ws=True, t=True))
        midVector=om.MVector(cmds.xform(poleTarget, query=True, ws=True, t=True))

        startEndVector=endVector - startVector
        print(startEndVector)

        startMidVector=midVector - startVector
        print(startMidVector)

        projection=(startMidVector*startEndVector.normal())*startEndVector.normal()
        print(projection)

        poleVectorDirection=(startMidVector-projection).normal()
        print(poleVectorDirection)

        poleVectorPosition=midVector + poleVectorDirection * distance
        print(poleVectorPosition)
        
        cmds.xform(ctrl, ws=True, t=(poleVectorPosition.x, poleVectorPosition.y, poleVectorPosition.z))
        cmds.poleVectorConstraint(ctrl, handleName)

def createIKSpline(jointStart, jointMid, jointEnd, splineName:str,
                   ctrlStart=None, ctrlMid=None, ctrlEnd=None,
                   jntNameStr:str='jnt', jntControlName:str='ctrlJnt',
                   createCustomCrv:bool=True, splineCurveName:str='ikSpline_crv',
                   rollTwist=True):
    
    if cmds.objectType(jointStart) != 'joint' or cmds.objectType(jointMid) != 'joint' or cmds.objectType(jointEnd) != 'joint':
        return None
    
    copyJoints=[]
    copyJoints.append(cmds.duplicate(jointStart, po=True, n=jointStart.replace(jntNameStr, jntControlName))[0])
    copyJoints.append(cmds.duplicate(jointMid, po=True, n=jointMid.replace(jntNameStr, jntControlName))[0])
    copyJoints.append(cmds.duplicate(jointEnd, po=True, n=jointEnd.replace(jntNameStr, jntControlName))[0])

    cmds.parent(copyJoints, world=True)
    cmds.joint(copyJoints, edit=True, orientJoint='none')
    # set joint rotation back to zero in case the joint isn't zero'd out
    for copyJnt in copyJoints:
        cmds.setAttr(f'{copyJnt}.rotateX', 0)
        cmds.setAttr(f'{copyJnt}.rotateY', 0)
        cmds.setAttr(f'{copyJnt}.rotateZ', 0)

    if createCustomCrv:
        cmds.select(cl=True)
        cmds.select(jointStart, hi=True)
        jntChain=cmds.ls(selection=True)
        cmds.select(cl=True)
        print(jntChain)

        points=[]
        for jnt in jntChain:
            jntPos=cmds.xform(jnt, query=True, ws=True, t=True)
            points.append(jntPos)
            if jnt==jointEnd:
                print(jnt)
                break
        if len(points)<=3:
            degrees=2
        else:
            degrees=3
        splineCurve=cmds.curve(n=splineCurveName, d=degrees, point=points)

        splineHandle=cmds.ikHandle(name=splineName, solver='ikSplineSolver', createCurve=False, parentCurve=False,
                      startJoint=jointStart, endEffector=jointEnd, curve=splineCurve,
                      rootOnCurve=True)[0]
        
    else:
        splineHandle=cmds.ikHandle(name=splineName, solver='ikSplineSolver', createCurve=True, parentCurve=False,
                      startJoint=jointStart, endEffector=jointEnd, curve=splineCurve,
                      rootOnCurve=True)[0]
    
    cmds.select(clear=True)
    cmds.skinCluster(copyJoints[0], copyJoints[1], copyJoints[2], splineCurve, n=splineName+'_skinCluster', 
                     bindMethod=0, skinMethod=0, normalizeWeights=1, maximumInfluences=3, toSelectedBones=True)
    
    if ctrlStart:
        cmds.parentConstraint(ctrlStart, copyJoints[0])
    if ctrlMid:
        cmds.parentConstraint(ctrlMid, copyJoints[1])
    if ctrlEnd:
        cmds.parentConstraint(ctrlEnd, copyJoints[2])

    if rollTwist:
        multDivNode=cmds.createNode('multiplyDivide', name=splineName+'_twist_offset_multDivide')
        cmds.setAttr(f'{multDivNode}.input2X', -1)
        cmds.connectAttr(f'{ctrlStart}.rotateY', f'{multDivNode}.input1X')

        pmaNode=cmds.createNode('plusMinusAverage', name=splineName+'_twist_offset_pma')
        cmds.connectAttr(f'{multDivNode}.outputX', f'{pmaNode}.input1D[0]')
        cmds.connectAttr(f'{ctrlEnd}.rotateY', f'{pmaNode}.input1D[1]')

        cmds.connectAttr(f'{pmaNode}.output1D', f'{splineHandle}.twist')
        cmds.connectAttr(f'{ctrlStart}.rotateY', f'{splineHandle}.roll')
        if ctrlMid:
            cmds.connectAttr(f'{ctrlMid}.rotateY', f'{pmaNode}.input1D[2]')

def createIKFKChain(jointStart, jointEnd, jntNameStr='jnt'):
    ''' Creates IK and FK duplicate joint chain and constraints the original chain to both. '''
    if cmds.objectType(jointStart) != 'joint' or cmds.objectType(jointEnd) != 'joint':
        return None
    jntChain=[]
    cmds.select(jointStart, hi=True)
    tempJntChain=cmds.ls(selection=True, type='joint')
    for tempJnt in tempJntChain:
        jntChain.append(tempJnt)
        if tempJnt in jointEnd:
            break

    if jntChain:
        ikChain=[]
        tempIKChain=cmds.duplicate(jntChain, parentOnly=True, name='temp_ik_jnt')
        for i, ikJnt in enumerate(tempIKChain):
            if jntNameStr in ikJnt:
                ikJntName=jntChain[i].replace(jntNameStr, 'ik_'+jntNameStr)
                cmds.rename(ikJnt, ikJntName)
            else:
                ikJntName=jntChain[i]+'_ik'
                cmds.rename(ikJnt, ikJntName)
            ikChain.append(ikJntName)

        fkChain=[]
        tempFKChain=cmds.duplicate(jntChain, parentOnly=True, name='temp_fk_jnt')
        for i, fkJnt in enumerate(tempFKChain):
            if jntNameStr in fkJnt:
                fkJntName=jntChain[i].replace(jntNameStr, 'fk_'+jntNameStr)
                cmds.rename(fkJnt, fkJntName)
            else:
                fkJntName=jntChain[i]+'_fk'
                cmds.rename(fkJnt, fkJntName)
            fkChain.append(fkJntName)

        for i, jnt in enumerate(jntChain):
            cmds.parentConstraint(ikChain[i], fkChain[i], jnt, n=jnt+'_ik_fk_constraint')

def createIKFKControls(jointStart, jointEnd, ctrlSize:int=15,
                       jntSearchStr:str='jnt', ctrlReplaceStr:str='ctrl',
                       colorIndex:int=6, shapeDirectory=None):
    ''' 
    Creates basic IK and FK controller chain for the provided joint chain with alignment, orientation and proper hierarchy.
    Shape Directory required for control shapes, must include 'shapes_cv.json'.
    '''
    if cmds.objectType(jointStart) != 'joint' or cmds.objectType(jointEnd) != 'joint':
        return None
    cmds.select(jointStart, hi=True)
    fkChain=cmds.ls(selection=True, type='joint')
    parentCtrl=None

    for jnt in fkChain:
        childJnt=cmds.listRelatives(jnt, type='joint')
        if childJnt:
            curveRotation=get_curve_rotation(childJnt)
            overrideColor=cmds.colorIndex(colorIndex, q=True)
            if jntSearchStr in jnt:
                ctrlName=jnt.replace(jntSearchStr, 'fk_'+ctrlReplaceStr)
            else:
                ctrlName='fk_'+jnt
            ctrl=shp.circleShape(name=ctrlName, 
                                 radius=ctrlSize, typeOverride=overrideColor)
            cmds.rotate(curveRotation[0], curveRotation[1], curveRotation[2], ctrl+'.cv[*]', os=True, r=True)
            ctrlNode=cmds.group(n=ctrl+'_zero', em=True)
            cmds.parent(ctrl, ctrlNode)
            cmds.matchTransform(ctrlNode, jnt)

            if parentCtrl:
                cmds.parent(ctrlNode, parentCtrl)
            parentCtrl=ctrl

            if jnt in jointEnd:
                curveRotation=get_curve_rotation(childJnt)
                if not shapeDirectory:
                    cmds.warning('No IK Shape Created')
                    return
                shapeData=dutil.load_data(shapeDirectory, 'shapes_cv.json')
                overrideColor=cmds.colorIndex(colorIndex, q=True)
                if jntSearchStr in jnt:
                    ctrlName=jnt.replace(jntSearchStr, 'ik_'+ctrlReplaceStr)
                else:
                    ctrlName='ik_'+jnt
                ctrl=shp.customShape(shapeData, shapeLabel='star',
                                     name=ctrlName, 
                                     radius=ctrlSize, typeOverride=overrideColor)
                cmds.rotate(curveRotation[0], curveRotation[1], curveRotation[2], ctrl+'.cv[*]', os=True, r=True)
                ctrlNode=cmds.group(n=ctrl+'_zero', em=True)
                cmds.parent(ctrl, ctrlNode)
                cmds.matchTransform(ctrlNode, jnt)
                break

def createFootPivots(footHandle, ankleHandle, ballHandle,
                     footJoint, ankleJoint, ballJoint,
                     mainControl,
                     prefix:str='', suffix:str=''):
    ''' Sets up foot pivot groups for handling ankle, ball and toe movement for IK controls. '''
    toeTapGrp=cmds.group(n=prefix+'toe_tap'+suffix, em=True)
    toeTapZero=cmds.group(toeTapGrp, n=prefix+'toe_tap'+suffix+'_zero')
    cmds.matchTransform(toeTapZero, ankleJoint)
    cmds.parent(toeTapZero, mainControl)
    cmds.parent([ankleHandle, ballHandle], toeTapGrp)

    heelPeelGrp=cmds.group(n=prefix+'heel_peel'+suffix, em=True)
    heelPeelZero=cmds.group(heelPeelGrp, n=prefix+'heel_peel'+suffix+'_zero')
    cmds.matchTransform(heelPeelZero, ankleJoint)
    cmds.parent(heelPeelZero, mainControl)
    cmds.parent(footHandle, heelPeelGrp)

    swivelGrp=cmds.group([toeTapZero, heelPeelZero], n=prefix+'swivel'+suffix, em=True)
    swivelZero=cmds.group(swivelGrp, n=prefix+'swivel'+suffix+'_zero')
    cmds.matchTransform(swivelZero, ankleJoint)
    cmds.parent(swivelZero, mainControl)
    cmds.parent([toeTapZero, heelPeelZero], swivelGrp)

    toeTipGrp=cmds.group(swivelZero, n=prefix+'toe_tip'+suffix, em=True)
    toeTipZero=cmds.group(toeTipGrp, n=prefix+'toe_tip'+suffix+'_zero')
    cmds.matchTransform(toeTipZero, ballJoint)
    cmds.parent(toeTipZero, mainControl)
    cmds.parent(swivelZero, toeTipGrp)

    ankleGrp=cmds.group(toeTipZero, n=prefix+'ankle'+suffix, em=True)
    ankleZero=cmds.group(ankleGrp, n=prefix+'ankle'+suffix+'_zero')
    cmds.matchTransform(ankleZero, footJoint)
    cmds.parent(ankleZero, mainControl)
    cmds.parent(toeTipZero, ankleGrp)

def setChannelBoxAttr(objs:list, translateAttr:bool=True, rotateAttr:bool=True, 
                          scaleAttr:bool=False, visAttr:bool=False):
    ''' Locks and hides channel box attributes for the object list based on the attribute type flags. '''
    for objName in objs:
        if not translateAttr:
            cmds.setAttr(f'{objName}.translateX', lock=True, keyable=False)
            cmds.setAttr(f'{objName}.translateY', lock=True, keyable=False)
            cmds.setAttr(f'{objName}.translateZ', lock=True, keyable=False)
        else:
            cmds.setAttr(f'{objName}.translateX', lock=False, keyable=True)
            cmds.setAttr(f'{objName}.translateY', lock=False, keyable=True)
            cmds.setAttr(f'{objName}.translateZ', lock=False, keyable=True)

        if not rotateAttr:
            cmds.setAttr(f'{objName}.rotateX', lock=True, keyable=False)
            cmds.setAttr(f'{objName}.rotateY', lock=True, keyable=False)
            cmds.setAttr(f'{objName}.rotateZ', lock=True, keyable=False)
        else:    
            cmds.setAttr(f'{objName}.rotateX', lock=False, keyable=True)
            cmds.setAttr(f'{objName}.rotateY', lock=False, keyable=True)
            cmds.setAttr(f'{objName}.rotateZ', lock=False, keyable=True)

        if not scaleAttr:
            cmds.setAttr(f'{objName}.scaleX', lock=True, keyable=False)
            cmds.setAttr(f'{objName}.scaleY', lock=True, keyable=False)
            cmds.setAttr(f'{objName}.scaleZ', lock=True, keyable=False)
        else:
            cmds.setAttr(f'{objName}.scaleX', lock=False, keyable=True)
            cmds.setAttr(f'{objName}.scaleY', lock=False, keyable=True)
            cmds.setAttr(f'{objName}.scaleZ', lock=False, keyable=True)
        
        if not visAttr:
            cmds.setAttr(f'{objName}.visibility', keyable=False)
        else:
            cmds.setAttr(f'{objName}.visibility', keyable=True)

def savePositions(vertSelectionList:list, setName:str):
    '''
    Returns a position set created from the vertex selection. 
    Selection list should only include vertex set.
    '''
    vertSelectionSet={}
    vertPositions=getVertPositions(vertSelectionList)
    vertSelectionSet[setName]=vertPositions
    return vertSelectionSet

def getVertPositions(selection:list):
    ''' Returns a list of each vertex position values from the provided selection. '''
    # use flatten flag to place the proper position values for each selected vert
    verts=cmds.ls(selection, flatten=True)
    # verify that the selection is not lower than 0 vertices before proceeding
    if len(verts) <= 0:
        return None
    else:
        verts_pos=[]
        for vert in verts:
            if '.vtx' not in vert:
                cmds.warning('selection set can only include vertices')
                return
            # get the specific 'x', 'y' or 'z' position values and store them
            vert_pos=cmds.xform(vert, q=True, ws=True, t=True)
            verts_pos.append(vert_pos)
        # sort from highest to least value of each every item using the direction position value 
        verts_pos.sort(key=lambda position: position)
        # verts_pos.sort()
        return verts_pos

