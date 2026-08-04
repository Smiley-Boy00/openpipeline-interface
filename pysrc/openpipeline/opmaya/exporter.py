import modules as md
from abc import ABC
import maya.cmds as mc
import maya.mel as mel
import sys
import os

class exporterType(ABC):
    ''' Base Class for building exporter type interfaces and its setting dependencies. '''
    def __init__(self):
        ''' Initialize methods and private dependencies. '''
        self._export_path = None
        self._file_name = None

        # create empty data set to store any incoming mesh's translation data values 
        self._obj_placement = {}

    def set_file_name(self, file_name: str):
        ''' Create unique file name. '''
        self._file_name=file_name

    def set_UE_project_path(self, ue_path:str, folder_name='MayaImports'):
        ''' Build export project path: 
            'c:/Unreal Engine/Active Project/Content/[folder_name]'. '''
        # create a path inside the UE's project contents folder where the mesh will be exported to
        self._export_path = os.path.join(ue_path, 'Content', folder_name)

        if not os.path.exists(self._export_path):
            os.makedirs(self._export_path)

    def move_sel_to_origin(self, obj_selection):
        ''' Move object to world origin: [0,0,0]. ''' 
        obj_parent=mc.listRelatives(obj_selection, parent=True)
        if mc.nodeType(obj_parent) != 'joint':
            # store object with their initial translation data values (location)
            self._obj_placement[obj_selection] = mc.xform(obj_selection, worldSpace=True, query=True, translation=True)
            md.move_to_origin(obj_selection)
        else:
            if not obj_parent:
                self._obj_placement[obj_selection] = mc.xform(obj_selection, worldSpace=True, query=True, translation=True)
                md.move_to_origin(obj_selection)

    def place_sel_to_original_pos(self, obj_selection):
        ''' Move object to initial translation data values (location). ''' 
        if self._obj_placement.get(obj_selection):
            translation=self._obj_placement.get(obj_selection)
            md.place_mesh_back(translation, obj_selection)

    def export(self):
        ''' Perform the type dependant export. '''
        if not self._export_path:
            self._export_path = md.get_documents_folder()

class fbx(exporterType):
    ''' 
    FBX exporter interface. 
    Enable mel.eval settings prior to executing export.
    '''
    def __init__(self):
        super().__init__()
        
        self._file_name='mayaExport.fbx'

        self._fbx_ver_set = {"FBX 2020": "FBX202000", "FBX 2019": "FBX201900",
                             "FBX 2018": "FBX201800", "FBX 2016/2017": "FBX201600",
                             "FBX 2014/2015": "FBX201400", "FBX 2013": "FBX201300",
                             "FBX 2012": "FBX201200", "FBX 2011": "FBX201100",
                             "FBX 2010": "FBX201000", "FBX 2009": "FBX200900"}
        
        mc.FBXResetExport()

    def get_fbx_versions(self) -> dict:
        ''' Return FBX version (key) values data set. '''
        return self._fbx_ver_set

    def export_bake_anim(self, start: int|None=None, end: int|None=None, value: bool=False):
        ''' 
        Enable or disable 'FBXExportBakeComplexAnimation' export bool value.
        Optionally set start and end frame values for baking animation. 
        '''
        mc.FBXExportBakeComplexAnimation('-v', value)
        mc.FBXExportBakeResampleAnimation('-v', value)
        if start:
            mc.FBXExportBakeComplexStart('-v', start)
        if end:
            mc.FBXExportBakeComplexEnd('-v', end)
        mc.FBXExportBakeComplexStep('-v', 1)
        
    def export_smoothing_groups(self, value: bool=False):
        ''' Enable or disable 'FBXExportSmoothingGroups' export bool value. '''
        mc.FBXExportSmoothingGroups('-v', value)

    def export_smooth_mesh(self, value: bool=False):
        ''' Enable or disable 'FBXExportSmoothMesh' export bool value. '''
        mc.FBXExportSmoothMesh('-v', value)

    def export_tangents_binormals(self, value: bool=False):
        ''' Enable or disable 'FBXExportTangents' export bool value. '''
        mc.FBXExportTangents('-v', value)

    def export_skinWeights(self, value: bool=False):
        ''' Enable or disable 'FBXExportSkins' export bool value. '''
        mc.FBXExportSkins('-v', value)
        
    def export_blendShapes(self, value: bool=False):
        ''' Enable or disable 'FBXExportShapes' export bool value. '''
        mc.FBXExportShapes('-v', value)

    def export_embedded_textures(self, value: bool=False):
        ''' Enable or disable 'FBXExportTextures' export bool value. '''
        mc.FBXExportEmbeddedTextures('-v', value)

    def triangulate(self, value: bool=False):
        ''' Enable or disable 'FBXExportTriangulate' export bool value. '''
        mc.FBXExportTriangulate('-v', value)

    def file_type(self, value: bool=False):
        ''' Enable or disable 'FBXExportInAscii' export bool value. '''
        mc.FBXExportInAscii('-v', value)

    def up_axis(self, value: bool=False):
        ''' Set mel.eval 'FBXExportUpAxis' export value to 'y' or 'z'. '''
        if value:
            mc.FBXExportUpAxis('y')
        else:
            mc.FBXExportUpAxis('z')
    
    def file_version(self, version: str="FBX 2018"):
        ''' Set mel.eval 'FBXExportFileVersion' export value to an existing FBX version.\n
            Versions:\n["FBX 2020", "FBX 2019", "FBX 2018", "FBX 2016/2017", 
                        "FBX 2014/2015", "FBX 2013", "FBX 2012", "FBX 2011", 
                        "FBX 2010", "FBX 2009"]. '''
        if version not in self._fbx_ver_set:
            raise ValueError(f'FBX version [{version}] not found or non-existent')
        
        # find the export value based on the version data set
        export_value=self._fbx_ver_set[version]
        print(f'Exported: {version} - {export_value}')
        mc.FBXExportFileVersion('-v', export_value)

    def exclude_anim(self):
        mc.FBXExportAnimationOnly('-v', False)
        mc.FBXExportBakeComplexAnimation('-v', False)
        mc.FBXProperty('Export|IncludeGrp|Animation', '-v', 0)

    def export(self):

        export_file = os.path.join(self._export_path, self._file_name)

        try:
            #'-f' stands for "File" & '-s' for "Selected"; export the selected mesh into a .fbx file
            mc.FBXExport('-f', export_file.replace('\\', '/'), '-s')

            # log execution
            sys.stdout.write("Export Successful: Open Unreal Project to Initialize Import\n")
        except Exception as e:
            sys.stderr.write(f"Export completed with warnings: {e}")

class obj(exporterType):
    ''' 
    OBJ exporter interface. 
    Set export bool flag values prior to executing export.
    '''
    def __init__(self):
        super().__init__()

        self._file_name='mayaExport.obj'
        
    def export(self,
               groups=0,
               pt_groups=0,
               materials=0,
               smoothing=0,
               normals=0,
               include_textures: bool=False):
        '''OBJ export values are interpreted as bool integers: 0 (False) or 1 (True)'''
        
        export_file = os.path.join(self._export_path, self._file_name)

        # store tuple values corresponding to each OBJ setting
        export_settings=(f'groups={groups};ptgroups={pt_groups};materials={materials};smoothing={smoothing};normals={normals}')

        # force export file
        # ignore non-crucial errors
        try:
            mc.file(export_file, force=True, options=export_settings, typ="OBJexport", 
                    preserveReferences=include_textures, exportSelected=True)
            
            # log execution
            sys.stdout.write("Export Successful: Open Unreal Project to Initialize Import\n")
        except Exception as e:
            sys.stderr.write(f"Export completed with warnings: {e}")
            
    
