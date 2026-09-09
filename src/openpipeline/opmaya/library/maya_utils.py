import maya.api.OpenMaya as om
import maya.cmds as mc


# maya modules dependent functions
def move_to_origin(mesh) -> None:
    ''' Moves the provided mesh to the world origin (0,0,0) using its rotate pivot. '''
    mc.move(0,0,0, mesh, rotatePivotRelative = True)

def place_mesh_back(values, mesh) -> None:
    ''' Moves the provided mesh back to its original position using provided values. '''
    mc.move(values[0],
            values[1],
            values[2], mesh, absolute=True)

def create_locator(name:str, 
                  prefix:str|None=None, suffix:str|None=None,
                  locScale:float=5):
    ''' 
    Creates a cluster object from the provided selection list and
    constrains a newly created locator to the cluster position. 
    Returns the locator transform name. 
    '''
    if prefix:
        # add prefix string to locator 
        name=prefix+name
    if suffix:
        # add suffix string to locator
        name+=suffix
    # create custom locator and obtain its transform node
    locShp=mc.createNode('cLocator', name=f'{name}_loc_shp')
    locTrn=mc.listRelatives(locShp, parent=True)[0]
    # set locator's local scale
    scaleID=['localScaleX', 'localScaleY', 'localScaleZ']
    for id in scaleID:
        mc.setAttr(f'{locShp}.{id}', locScale)
    # store full name in ID 
    locObjID=name
    # rename locator's transform
    mc.rename(locTrn, locObjID)
    mc.select(clear=True)
    return locObjID

def constrain_locator_to_cluster(selectionLs:list, clusterName:str, locObj:str):
    ''' 
    Creates single cluster based on the selection list to point constrain a locator to it.
    Deletes cluster after constraint.
    '''
    # use flatten flag to store selection values a sequential list (i.e. vtx[], vtx[], vtx[])
    dataSelection=mc.ls(selectionLs, flatten=True)
    if not dataSelection:
        return 
    clusterObj=mc.cluster(dataSelection, name=f'{clusterName}_cls')
    # constrain locator to cluster position then delete constraint
    mc.pointConstraint(clusterObj, locObj)
    mc.delete(clusterObj)

def joint_chain(startVector:om.MPoint, endVector:om.MPoint, 
                    jntNames:list=['start', 'end'],
                    jntNums:int=2, parentJnt=None, 
                    orientJoint:str='xyz', secAxisOrient:str='yup', 
                    rotationOrder:str='xyz', jntsRad:float=3,
                    prefix:str|None=None, suffix:str|None=None,
                    overrideColor:int|None=None):
    ''' Creates a joint chain between two provided locator positions. '''
    # verify that the script doesn't create a single joint, must be a two joint chain at minimum
    if jntNums < 2:
        mc.warning('Number of Joints cannot be lesser than 1')
        return

    mc.select(clear=True)
    # select parent joint if provided to connect the new joint chain to it
    if parentJnt:
        mc.select(parentJnt)
    
    createdJnts=[]
    for n in range(jntNums):
        jntName=jntNames[n]

        if n==0 and mc.objExists(jntName):
             mc.select(jntName)
             createdJnts.append(jntName)
        else:
            # obtain interpolation ratio
            ratio=float(n) / (jntNums - 1)

            # use lerp formula to find joint (x,y,z) position: [initialPosition+(totalDistance)*percentageTraveled]
            jntPos=[startVector.x + (endVector.x-startVector.x) * ratio,
                    startVector.y + (endVector.y-startVector.y) * ratio,
                    startVector.z + (endVector.z-startVector.z) * ratio]

            if prefix:
                # add prefix string to joint
                jntName=prefix+jntName
            if suffix:
                # add suffix string to joint
                jntName+=suffix

            # create joint at calculated position with numbered naming convention
            newJnt=mc.joint(name=jntName, p=jntPos, rad=jntsRad)
            createdJnts.append(newJnt)

    # obtain start and end joint names
    startJnt, endJnt = createdJnts[0], createdJnts[-1]
    # set joint orientation for the entire chain except
    mc.joint(startJnt, edit=True, orientJoint=orientJoint, 
               secondaryAxisOrient=secAxisOrient, rotationOrder=rotationOrder, children=True)
    # zero out the rotation of the very last joint so it aligns with the world or parent
    mc.joint(endJnt, edit=True, orientJoint='none', children=True)
    
    mc.select(clear=True)

    if overrideColor:
        mc.setAttr(f'{startJnt}.overrideEnabled', True)
        mc.setAttr(f'{startJnt}.overrideColor', overrideColor)
    return createdJnts

def aim_constrain_locators(locStartName:str, locEndName:str,
                aimVector:list=[1,0,0], upVector:list=[0,1,0],
                worldUpVector:list=[0,1,0]):
    ''' 
    Sets aim constraints between two locators.
    Locators aim at each other to simulate parent/child joint orientation relationship.
    '''
    # get locator parent & aim constraints, delete each if any exists
    startConstraints=[]
    if mc.listRelatives(locStartName, type='parentConstraint'):
        startConstraints.append(*mc.listRelatives(locStartName, type='parentConstraint'))
    if mc.listRelatives(locStartName, type='aimConstraint'):
        startConstraints.append(*mc.listRelatives(locStartName, type='aimConstraint'))
    if startConstraints:
        for constraint in startConstraints:
            mc.delete(constraint)

    # get locator parent & aim constraints, delete each if any exists
    endConstraints=[]
    if mc.listRelatives(locEndName, type='parentConstraint'):
        endConstraints.append(mc.listRelatives(locEndName, type='parentConstraint'))
    if mc.listRelatives(locEndName, type='aimConstraint'):
        endConstraints.append(mc.listRelatives(locEndName, type='aimConstraint'))
    if endConstraints:
        for constraint in endConstraints:
            mc.delete(constraint)

    # make start locator aim at end locator
    mc.aimConstraint(locEndName, locStartName, aim=aimVector, u=upVector, wu=worldUpVector)
    # create negative aim vector for end locator to aim at start locator
    negAimVector=[val*(-1) for val in aimVector]
    mc.aimConstraint(locStartName, locEndName, aim=negAimVector, u=upVector, wu=worldUpVector)

def parent_locator_to_joint(jntName:str, locName:str):
    ''' 
    Constrains a locator to a joint using parent constraint.
    Deletes any relevant constraints before applying new ones.
    '''
    # get locator & joint constraints, delete each if any exists
    locConstraints=mc.listRelatives(locName, type='aimConstraint')
    jntConstraints=mc.listRelatives(jntName, type='parentConstraint')
    if jntConstraints:
        print(jntConstraints)
        for constraint in jntConstraints:
            mc.delete(constraint)
    if locConstraints:
        for constraint in locConstraints:
            mc.delete(constraint)
    
    mc.parentConstraint(jntName, locName)

def mirror_joints(mirrorAxis:str='YZ', mirrorFunc:str='Behavior',
                 search:str='', replace:str='', includeLocators:bool=False):
    ''' 
    Sets up joint mirroring based on provided axis and function. 
    Returns a list of the newly created mirrored joint chain.
    '''
    mirrorAxisVal, mirrorFuncVal = ('XY','XZ','YZ'), ('Behavior', 'Orientation')
    if mirrorAxis not in mirrorAxisVal or mirrorFunc not in mirrorFuncVal:
        raise ValueError('Wrong value given for mirrorAxis or mirrorFunc')
    
    jntSelection=mc.ls(selection=True, type='joint')
    if not jntSelection:
        return None

    searchReplace=(search, replace)

    if mirrorAxis=='XY':
        mc.mirrorJoint(mxy=True, mb=True, sr=searchReplace) if mirrorFunc == 'Behavior' else mc.mirrorJoint(mxy=True, mb=False, sr=searchReplace)
    elif mirrorAxis=='XZ':
        mc.mirrorJoint(mxz=True, mb=True, sr=searchReplace) if mirrorFunc == 'Behavior' else mc.mirrorJoint(mxz=True, mb=False, sr=searchReplace)
    else:
        mc.mirrorJoint(myz=True, mb=True, sr=searchReplace) if mirrorFunc == 'Behavior' else mc.mirrorJoint(myz=True, mb=False, sr=searchReplace)
    
    mc.select(hi=True)
    mirroredChain=mc.ls(selection=True, type='joint')
    
    if includeLocators:
        mirroredSet={}
        # select joint hierarchy
        mc.select(jntSelection, hi=True)
        jntChain=mc.ls(selection=True, type='joint')
        for i, jnt in enumerate(jntChain):
            constraints=mc.listConnections(jnt, type='parentConstraint')
            for constraint in constraints:
                node=mc.listConnections(constraint)[0]
                nodeShp=mc.listRelatives(node, type='shape')[0]
                if mc.nodeType(nodeShp)=='cLocator' or mc.nodeType(nodeShp)=='locator':
                    mirroredSet[mirroredChain[i]]=[node.replace(search, replace), mc.getAttr(f'{nodeShp}.localScaleX')]
                    break
        print(mirroredSet)
        if mirroredSet:
            # create each mirrored locator
            for jnt in mirroredSet:
                locName=mirroredSet.get(jnt)[0]
                locScale=mirroredSet.get(jnt)[1]
                create_locator(locName, locScale=locScale)
                parent_locator_to_joint(jnt, locName)
    
    return mirroredChain

def get_curve_rotation(childJoints:list):
    ''' Finds the control's orientation based on the joint children. '''
    if len(childJoints) < 2: # joint has only one child
        # get the absolute values of the joint's position/location
        childJointPos = (abs(mc.getAttr(childJoints[0] + '.translateX')),
                         abs(mc.getAttr(childJoints[0] + '.translateY')),
                         abs(mc.getAttr(childJoints[0] + '.translateZ')))
        
        # analyze the max translation value and set the rotation axis for the controller curve 
        jointLength = max(childJointPos)
        if childJointPos.index(jointLength) == 0:
            # curve rotation in x-axis
            curveRotation = (0, 0, 90)
        if childJointPos.index(jointLength) == 1:
            # no curve rotation, y-axis
            curveRotation = (0, 0, 0)
        if childJointPos.index(jointLength) == 2:
            # curve rotation in z-axis
            curveRotation = (90, 0, 0)
    
    else: # joint has multiple children
        # get list comprehension of each axis absolute position value for each child joint
        childJointPosX = [abs(mc.getAttr(jnt + '.translateX')) for jnt in childJoints]
        childJointPosY = [abs(mc.getAttr(jnt + '.translateY')) for jnt in childJoints]
        childJointPosZ = [abs(mc.getAttr(jnt + '.translateZ')) for jnt in childJoints]
        
        # get the absolute values of the joint's position/location based on the sum divided by the amount of all child joints
        childJointPos = [sum(childJointPosX)/len(childJointPosX),
                         sum(childJointPosY)/len(childJointPosY),
                         sum(childJointPosZ)/len(childJointPosZ)]
        
        # analyze the max translation value and set the rotation axis for the controller curve 
        jointLength = max(childJointPos)
        if childJointPos.index(jointLength) == 0:
            # curve rotation in x-axis
            curveRotation = (0, 0, 90)
        if childJointPos.index(jointLength) == 1:
            # no curve rotation, y-axis
            curveRotation = (0, 0, 0)
        if childJointPos.index(jointLength) == 2:
            # curve rotation in z-axis
            curveRotation = (90, 0, 0)

    # check if length is 0 
    if jointLength < 0.1:
        jointLength = 1.0
        
    return curveRotation

def get_root_jnts() -> list:
    ''' Returns a list of root joints found in the current scene. '''
    scene_joints=mc.ls(type='joint')

    if not scene_joints:
        print("No joints found")
        
    root_joints=[]
    for joint in scene_joints:
        # if joint has no parent or parent is not a joint, store root joint
        parent_jnt=mc.listRelatives(joint, parent=True, fullPath=True)
        if not parent_jnt or mc.nodeType(parent_jnt[0]) != 'joint':
            root_joints.append(joint)

    return root_joints

def select_root_jnt(root_jnt:str, contains_list:bool=False, jnts:list=[]) -> None:
    ''' 
    Checks root joint exists and selects it.
    Contains_list must be True to deselect provided joint list.
    '''
    if contains_list:
        for jnt in jnts:
            if mc.objExists(jnt):
                mc.select(jnt, deselect=True)
    else:
        mc.warning('Must provide a joint list to deselect.')

    if not mc.objExists(root_jnt):
        print('Nothing Selected')
    else:
        mc.select(root_jnt, add=True)
        print(f'{root_jnt} Selected')

def get_unused_joints_in_hier(root_jtns:list):
    ''' 
    Returns a list of joints that have no bind data. 
    Requires a joint hierarchy list.
    '''
    unbinded_jnts={}
    for root_jnt in root_jtns:
        if mc.nodeType(root_jnt) != 'joint':
            continue
        if not mc.objExists(root_jnt):
            continue

        hierarchy=mc.listRelatives(root_jnt, allDescendents=True, type='joint', fullPath=True)

        hierarchy.append(root_jnt)

        unused_jnts = []

        for jnt in hierarchy:
            is_bound=False
            connections=mc.listConnections(f'{jnt}.worldMatrix[0]', type='skinCluster')

            if connections:
                is_bound=True

            if not is_bound:
                unused_jnts.append(jnt)
        unbinded_jnts[root_jnt]=unused_jnts

    return unbinded_jnts

def bind_unused_joints(root_jnts_data:dict):
    '''
    Binds the joints that have no bind data.
    Requires a dictionary of unused joints in hierarchy.
    '''
    for root_jnt in root_jnts_data:
        connections=mc.listConnections(f'{root_jnt}.worldMatrix[0]', type='skinCluster')
        if not connections:
            hierarchy=mc.listRelatives(root_jnt, allDescendents=True, type='joint', fullPath=True)
            for jnt in hierarchy:
                connections=mc.listConnections(f'{jnt}.worldMatrix[0]', type='skinCluster')
                if connections:
                    break
        print(connections)
    
    for unbinded_joint in root_jnts_data.get(root_jnt):
        for connected_cluster in connections:
            mc.skinCluster(connected_cluster, edit=True, 
                           addInfluence=unbinded_joint, 
                           weight=0.0, lockWeights=False)

def get_skinned_meshes(selection:list) -> list:
        ''' Returns a list of skinned meshes from the provided selection. '''
        skinned_meshes=[]

        for mesh in selection:
            # if item is a mesh, get shape nodes
            shapes = mc.listRelatives(mesh, shapes=True, fullPath=True)
            if shapes:
                for shape in shapes:
                    if mc.nodeType(shape) == 'mesh':
                        # find skin cluster connection
                        clusters = mc.ls(mc.listConnections(shape, type='skinCluster'), 
                                        type='skinCluster')
                    
                        if clusters:
                            skinned_meshes.append(mesh)
                            break # stop checking other shapes if one is skinned

        return skinned_meshes

def del_non_deform_history(mesh_sl:list) -> None:
    ''' Deletes non-deformer history of the provided selection list. '''
    for obj in mesh_sl:
        if mc.nodeType(obj) != 'mesh':
            continue
        # deletes the non-derformer history of the selected mesh
        mc.bakePartialHistory(obj, prePostDeformers=True)