import maya.cmds as mc
from pathlib import Path
import json
import os

# Module/functions library for all the plugin modules

# maya modules dependent functions
def move_to_origin(mesh) -> None:
    ''' Moves the provided mesh to the world origin (0,0,0) using its rotate pivot. '''
    mc.move(0,0,0, mesh, rotatePivotRelative = True)

def place_mesh_back(values, mesh) -> None:
    ''' Moves the provided mesh back to its original position using provided values. '''
    mc.move(values[0],
            values[1],
            values[2], mesh, absolute=True)
    
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

# data handling related functions
def save_data(path:str, file_name:str, data) -> None:
    ''' Saves data into a json file: must include a path to store data. '''
    if not file_name.endswith('.json'):
        file_name+='.json'

    with open(os.path.join(path, file_name), 'w') as file:
        json.dump(data, file, indent=4, sort_keys=True)

def load_data(path:str, file_name:str) -> dict:
    ''' Loads a path data (dictionary) from a json file. '''
    with open(os.path.join(path, file_name), 'r') as file:
        stored_data = json.load(file)

    return stored_data

# directory related functions
def get_documents_folder() -> str:
    ''' Finds the documents path inside the user's home directory. '''
    documents_path = os.path.join(str(Path.home()), 'Documents')
    return documents_path

def path_exists(file_path: str) -> bool:
    ''' Checks if a path or file path exists. '''
    if os.path.exists(file_path):
        return True
    
    else:
        return False
    

