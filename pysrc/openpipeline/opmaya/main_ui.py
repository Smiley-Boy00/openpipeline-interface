import maya.cmds as mc
import os
import sys
# import package dependent modules
from ..maya import modules as md
from ..maya import exporter

class clipsElementsUI():
    ''' Class to handle animation clip UI elements inside the main exporter UI.'''
    def __init__(self):
        ''' Initializes the clip elements UI data and variables. '''
        self.text_elements={'clip_text':'Clip File Name', 'start_text':'Start', 'end_text':'End', 'empty_01':'', 'empty_02':''}
        self.element_names=['clipName_', 'clipStart_', 'clipEnd_', 'clipAdd_', 'clipDel_']
        self.newest_row=0 
        self.clips_created={} 
        self.initial_add_icon_click=False 
        
    def build_base_elements(self, parentUI:str):
        ''' Builds or unhides the base clip elements UI layout structure. '''
        # build layout to contain clip rows
        if mc.control('maya_clips_scroll', exists=True):
            mc.control('maya_clips_scroll', edit=True, vis=True)
        else:
            mc.scrollLayout('maya_clips_scroll', parent=parentUI,
                            childResizable=True, panEnabled=True, 
                            height=100, vis=True,
                            horizontalScrollBarThickness=16,
                            verticalScrollBarThickness=16,
                            verticalScrollBarAlwaysVisible=True)
            
            mc.rowColumnLayout('clips_rowColumn', adj=1, 
                               columnOffset=[1, 'left', 10], nc=5,  
                               parent='maya_clips_scroll', vis=True)
        
        # show or create the text header elements
        for text_element in self.text_elements:
            if mc.control(text_element, exists=True):
                mc.control(text_element, edit=True, vis=True, en=True)
            else:
                mc.text(text_element, align='center', label=self.text_elements.get(text_element))
        self.create_or_delete_initial_fields()
    
    def create_fields(self, row_num:int):
        ''' Creates a new row of clip elements with unique numbered IDs for row callback. '''
        if row_num==0:
            raise ValueError('Row iteration int:0 should not be called.')

        # disable exporter UI elements that clash with clips export
        mc.control('filename_field', edit=True, vis=False)
        mc.checkBox('batch_export', edit=True, en=False, value=False)

        main_elementIDs=[]
        for name in self.element_names:
            element=name+f'{row_num}'
            # check if element already exists and enable it
            if mc.control(element, exists=True):
                mc.control(element, edit=True, en=True)

            else:
                # get current scene frame range to set as default clip range values
                start_frame = mc.playbackOptions(query=True, minTime=True)
                end_frame = mc.playbackOptions(query=True, maxTime=True)
                # create corresponding clip element based on its name
                if 'clipName_' in element:
                    mc.textFieldGrp(element, parent='clips_rowColumn', 
                                    pht='Add clip file name', adjustableColumn=1)
                    main_elementIDs.append(element)
                if 'clipStart_' in element:
                    mc.intFieldGrp(element, parent='clips_rowColumn', numberOfFields=1, v1=start_frame)
                    main_elementIDs.append(element)
                elif 'clipEnd_' in element:
                    mc.intFieldGrp(element, parent='clips_rowColumn', numberOfFields=1, v1=end_frame)
                    main_elementIDs.append(element)
                elif 'clipAdd_' in element:
                    mc.iconTextButton(element, parent='clips_rowColumn', 
                                      style='iconOnly', image1='addCreateGeneric.png',
                                      c=lambda *args: self.add_new_fields_column(row_num=row_num))
                    main_elementIDs.append(element)
                elif 'clipDel_' in element:
                    mc.iconTextButton(element, parent='clips_rowColumn', 
                                      style='iconOnly', image1='trash.png',
                                      c=lambda *args: self.delete_fields_column(row_num=row_num))
        # store created row elements 
        self.clips_created[f'clip_{row_num}']=main_elementIDs

        # disable add icons from every other row except the newest one   
        for clip_row in self.clips_created:
            if clip_row==f'clip_{row_num}':
                continue
            for clip_element in self.clips_created.get(clip_row):
                if 'Add' in clip_element:
                    mc.control(clip_element, edit=True, enable=False)

    def delete_fields_column(self, row_num:int):
        ''' Deletes the numbered row of clip elements and updates the UI. '''
        # remove each element in the row
        for name in self.element_names:
            element=name+f'{row_num}'
            mc.deleteUI(element)
        # remove row from clips dictionary
        self.clips_created.pop(f'clip_{row_num}')

        # if the newest row was deleted, find the newest active row and enable its add icon
        if row_num==self.newest_row:
            active_rows=[]
            # get active rows
            for clip_row in self.clips_created:
                active_rows.append(int(clip_row.split('_')[-1]))
            if active_rows:
                # get highest active row number value
                active_row=max(active_rows)
                # enable add icon of newest active row
                mc.control(f'clipAdd_{active_row}', edit=True, enable=True)
                # set newest row to active row
                self.newest_row=active_row
            else:
                # no clips left, reset interface and trackers
                self.initial_add_icon_click=False
                self.create_or_delete_initial_fields()
                # re-enable exporter UI elements
                mc.control('filename_field', edit=True, vis=True)
                mc.checkBox('batch_export', edit=True, en=True)
                # reset newest row tracker
                self.newest_row=0

    def create_or_delete_initial_fields(self, delete:bool=False):
        ''' Handles the state of the initial clip elements row. '''
        # get each clip element
        for name in self.element_names:
            element=name+'0'
            if delete:
                if mc.control(element, exists=True):
                    mc.deleteUI(element)
            else:
                if mc.control(element, exists=True):
                    # skip delete icon element
                    if 'clipDel_' in element:
                        continue
                    else:
                        # make element visible
                        mc.control(element, edit=True, vis=True)

                else:
                    # create corresponding clip element based on its name
                    if 'clipName_' in element:
                        mc.textFieldGrp(element, parent='clips_rowColumn', adjustableColumn=1, en=False)
                    if 'clipStart_' in element:
                        mc.intFieldGrp(element, parent='clips_rowColumn', numberOfFields=1, en=False)
                    elif 'clipEnd_' in element:
                        mc.intFieldGrp(element, parent='clips_rowColumn', numberOfFields=1, en=False)
                    elif 'clipAdd_' in element:
                        mc.iconTextButton(element, parent='clips_rowColumn', 
                                            style='iconOnly', image1='addCreateGeneric.png', en=True,
                                            c=lambda *args: self.add_new_fields_column(row_num=0))
                    elif 'clipDel_' in element:
                        mc.iconTextButton(element, parent='clips_rowColumn', 
                                            style='iconOnly', image1='trash.png',
                                            en=False, vis=False)

    def add_new_fields_column(self, row_num:int):
        ''' 
        Calls creation of a new row of clip elements and manages UI trackers. 
        Checks if initial add icon has been clicked and calls to remove initial fields.
        '''
        if not self.initial_add_icon_click:
            row_num+=1 # first row has to be 1-based to avoid UI iteration conflict
            # remove initial fields to show only new fields row
            self.create_or_delete_initial_fields(delete=True)
            self.initial_add_icon_click=True

        if mc.control(f'clipAdd_{row_num}', exists=True):
            # increment row number to avoid number ID conflict 
            row_num+=1
        print(f'new clip row created: row {row_num}')
        self.create_fields(row_num)
        self.newest_row=row_num
        
    def get_clips_created(self):
        ''' Returns created clips data if any clips have been created. '''
        if not self.initial_add_icon_click:
            return None
        else:
            return self.clips_created

class mtouExporterUI():
    '''
    Class to handle UI display for exporter types.
    Executes modules once a project path data is instantiated.
    Generates import data after execution.
    '''
    def __init__(self):
        ''' Initializes the tool's UI layout, elements and class dependencies. '''
        print('Running MtoU Exporter Version: 0.3.0 ')

        # locate the user's home\Documents path
        self.folder_path = os.path.join(md.get_documents_folder(), 'UE', 'Data')
        
        # import exporter classes
        self.fbx = exporter.fbx()
        self.obj = exporter.obj()
        # import animation clips settings UI
        self.clipsUI = clipsElementsUI()

        self.window_ID = "EXPORTER"
        self.title = "Maya to Unreal Exporter v0.3"
        self.size = (600,650)
        
        # dictionaries to store and handle UI layouts & elements 
        self.checkerSettings = {}
        self.menuSettings = {}
        self.frameLayouts = {}
        # list to store and handle separator elements 
        self.separators = []

        if mc.window(self.window_ID, exists=True):
            mc.deleteUI(self.window_ID, window=True)

        self.windowDisplay = mc.window(self.window_ID, 
                                       title=self.title, 
                                       widthHeight=self.size, sizeable=True)

        # form layout to allow precision in handling UI elements 
        self.main_layout = mc.formLayout(parent=self.windowDisplay)

        # create tab option menu to contain exporter types as menu item elements
        self.exportType_menu = mc.optionMenu(label='Export:', 
                                            changeCommand=self.change_export_type)
        mc.menuItem(label="FBX")
        mc.menuItem(label="OBJ")

        # create fields to input the file and folder name of the exported asset  
        self.filename_field = mc.textFieldGrp('filename_field', label='File Name:', 
                                              placeholderText = 'Name your .fbx file',
                                              adjustableColumn=2,
                                              columnAlign=[1, 'left'],
                                              columnWidth=[1, 55])
        self.foldername_field = mc.textFieldGrp(label='Folder Name:', 
                                                placeholderText = 'Folder name inside the Content path',
                                                adjustableColumn=2,
                                                columnAlign=[1, 'left'],
                                                columnWidth=[1, 70])
        
        self.prefix_field = mc.textFieldGrp(label='Prefix: ', placeholderText = 'Prefix_',
                                            adjustableColumn=2,
                                            columnAlign=[1, 'left'],
                                            columnWidth2=[35, 100],)
        self.suffix_field = mc.textFieldGrp(label='Suffix: ', placeholderText = '_Suffix',
                                            adjustableColumn=2,
                                            columnAlign=[1, 'left'],
                                            columnWidth2=[35, 100])

        self.create_or_show_checkbox('batch_export', self.main_layout, label='Export Selected into Separate Files',
                                     checkerValue=False, separator=False)
        
        # connect checker identifier to it's boolean value for precise handling and callback
        self.checkerSettings['batch_export'] = False

        # create list comprehension of all the available FBX Maya export versions
        self.fbx_versions=[version for version in self.fbx.get_fbx_versions()]
        
        # build Maya export option settings frame grid layout
        self.maya_frame = mc.frameLayout(label='Maya Export Settings', 
                                         collapsable = True,
                                         backgroundColor=(0.25,0.46,0.88),
                                         highlightColor=(0.25,0.46,0.88),
                                         marginWidth=10,
                                         parent=self.main_layout)

        self.maya_column = mc.columnLayout(adjustableColumn=True)
        self.maya_checker_row = mc.rowLayout(numberOfColumns=4, generalSpacing=25,
                                           adjustableColumn=2, columnAlign=(4, 'right'))

        # columns parented to row layout create grid layout for check box element placement 
        self.left_maya_column = mc.columnLayout(adjustableColumn=True, 
                                                parent=self.maya_checker_row)
        self.centerLeft_maya_column = mc.columnLayout(adjustableColumn=True, 
                                                      parent=self.maya_checker_row)
        self.centerRight_maya_column = mc.columnLayout(adjustableColumn=True, 
                                                       parent=self.maya_checker_row)
        self.right_maya_column = mc.columnLayout(adjustableColumn=True, 
                                                 parent=self.maya_checker_row)
        # build row column to indicate additional Maya check box settings
        self.maya_rowColumn = mc.rowColumnLayout(nc=4, columnOffset=[1, 'left', 1],
                                                 columnAttach=[2, 'left', 25],
                                                 columnSpacing=[3, 25],
                                                 parent=self.maya_column, vis=True)

        # build Unreal import option settings frame grid layout
        self.unreal_frame = mc.frameLayout(label='Unreal Import Settings', 
                                           collapsable = True,
                                           backgroundColor=(0.15,0.18,0.20),
                                           highlightColor=(0.15,0.18,0.20),
                                           marginWidth=10,
                                           parent=self.main_layout)

        self.unreal_column = mc.columnLayout(adjustableColumn = True)
        self.unreal_checker_row = mc.rowLayout(numberOfColumns=4, generalSpacing=25, 
                                    adjustableColumn=2, columnAlign=(4, 'right'))

        self.left_unreal_column = mc.columnLayout(adjustableColumn=True, 
                                                  parent=self.unreal_checker_row)
        self.centerLeft_unreal_column = mc.columnLayout(adjustableColumn=True, 
                                                        parent=self.unreal_checker_row)
        self.centerRight_unreal_column = mc.columnLayout(adjustableColumn=True, 
                                                         parent=self.unreal_checker_row)
        self.right_unreal_column = mc.columnLayout(adjustableColumn=True, 
                                                   parent=self.unreal_checker_row)
        
        # display default settings UI when initializing
        # priority to FBX settings 
        self.build_fbx_ui_settings()

        # build utility button elements
        self.check_current_button = mc.button(label='Current UE Project', 
                                              command=self.reload_ue_data, parent=self.main_layout)
        self.export_button = mc.button(label='Export To Unreal', 
                                       command=self.do_FBX_export, parent=self.main_layout)

        # align and place the layout's frames and elements in the display window    
        mc.formLayout(self.main_layout, edit=True, attachForm = [(self.exportType_menu, 'left', 5), (self.exportType_menu, 'top', 10),
                                                                 (self.filename_field, 'left', 5), (self.filename_field, 'right', 5),
                                                                 (self.foldername_field, 'left', 5), (self.foldername_field, 'right', 5),
                                                                 (self.prefix_field, 'left', 150), ],
                                                    attachControl = [(self.filename_field, 'top', 10, self.exportType_menu),
                                                                     (self.foldername_field, 'top', 5, self.filename_field),
                                                                     (self.prefix_field, 'top', 5, self.foldername_field),
                                                                     (self.suffix_field, 'top', 5, self.foldername_field),
                                                                     (self.suffix_field, 'left', 15, self.prefix_field),])
        
        mc.formLayout(self.main_layout, edit=True, attachForm = [('batch_export', 'left', 210), ('batch_export', 'right', 5),
                                                                 (self.maya_frame, 'left', 5), (self.maya_frame, 'right', 5),
                                                                 (self.unreal_frame, 'left', 5), (self.unreal_frame, 'right', 5),],
                                                    attachControl = [('batch_export', 'top', 5, self.prefix_field),
                                                                     (self.maya_frame, 'top', 10, 'batch_export'),
                                                                     (self.unreal_frame, 'top', 10, self.maya_frame),])
        
        mc.formLayout(self.main_layout, edit=True, attachForm = [(self.export_button, 'left', 5), (self.export_button, 'right', 5),
                                                                (self.export_button, 'bottom', 5),
                                                                (self.check_current_button, 'left', 5), (self.check_current_button, 'right', 5),
                                                                (self.check_current_button, 'bottom', 5)],
                                                    attachControl = [(self.check_current_button, 'bottom', 8, self.export_button)])

        mc.showWindow()

    def build_fbx_ui_settings(self):
        ''' Handles the UI elements of the FBX export and import settings. '''
        # build check box elements for export settings 
        self.create_or_show_checkbox('smooth_groups', 'maya', label='Smoothing Groups', position='left', checkerValue=True)
        self.create_or_show_checkbox('smooth_mesh', 'maya', label='Smooth Mesh', position='left', checkerValue=False)
        self.create_or_show_checkbox('tangents', 'maya', label='Tangents and Binormals', position='centerLeft', checkerValue=True)
        self.create_or_show_checkbox('triangulate', 'maya', label='Triangulate', position='centerLeft', checkerValue=False)
        self.create_or_show_checkbox('move_to_origin', 'maya', label='Move to Origin', position='centerRight', checkerValue=True)
        self.create_or_show_checkbox('embed_media', 'maya', label='Embed Textures', position='centerRight', checkerValue=True)
        self.create_or_show_checkbox('skins', 'maya', label='Skinning', position='right', checkerValue=True)
        self.create_or_show_checkbox('blnd_shapes', 'maya', label='Blend Shapes', position='right', checkerValue=True)

        if mc.control('middle_separator_01', exists=True):
            mc.control('middle_separator_01', edit=True, visible=True)
        else:
            middle_separator_01 = mc.separator('middle_separator_01', style='none', 
                                               height=7.5, parent=self.maya_column)
            self.separators.append(middle_separator_01)

        self.create_or_show_checkbox('unused_jnts', self.maya_rowColumn, label='Bind Unused Joints', checkerValue=False, 
                                     separator=False)

        export_anim_id='export_anim'
        maya_anim_frame_id='maya_anim_frame'
        # animation export checkbox handles animation clip settings visibility
        self.create_or_show_checkbox(export_anim_id, self.maya_rowColumn, label='Export Animation', checkerValue=False,
                                     separator=False,
                                     onCommand=lambda arg:self.export_anim_state(state=True),
                                     offCommand=lambda arg:self.export_anim_state())
        # build animation clips frame layout, hidden by default
        # unhide layout if it already exists
        if not mc.control(maya_anim_frame_id, exists=True):
            maya_anim_frame = mc.frameLayout(maya_anim_frame_id, parent=self.maya_column, label='Animation Clips', 
                                             visible=False, collapsable=True, collapse=True, 
                                             backgroundColor=(0.12,0.12,0.16), marginWidth=15,)
            self.frameLayouts[maya_anim_frame_id] = maya_anim_frame

        # show layout and checkbox if export animation was previously checked
        if mc.checkBox(export_anim_id, query=True, value=True):
            mc.control('bake_anim', edit=True, vis=True, en=True)
            mc.control(maya_anim_frame_id, edit=True, vis=True)
        
        if mc.control('middle_separator_02', exists=True):
            mc.control('middle_separator_02', edit=True, visible=True)
        else:
            middle_separator_02 = mc.separator('middle_separator_02', style='single', 
                                            height=7.5, 
                                            parent=self.maya_column)
            self.separators.append(middle_separator_02)
        if mc.control('middle_separator_03', exists=True):
            mc.control('middle_separator_03', edit=True, visible=True)
        else:
            middle_separator_03 = mc.separator('middle_separator_03', style='none', 
                                            height=7.5, 
                                            parent=self.maya_column)
            self.separators.append(middle_separator_03)
        
        # build option menu elements export settings
        self.create_or_show_menu('axis', 'maya', label='Up Axis:', items=['Y-Up', 'Z-Up'])
        self.create_or_show_menu('fileType', 'maya', label='FBX File Type:', items=['Binary', 'Ascii'])
        self.create_or_show_menu('version', 'maya', label='FBX Version:', items=self.fbx_versions)

        # build check box elements for import settings 
        self.create_or_show_checkbox('imp_materials', 'unreal', label='Include Materials', position='centerLeft', checkerValue=True)
        self.create_or_show_checkbox('imp_textures', 'unreal', label='Include Textures', position='centerLeft', checkerValue=True)
        self.create_or_show_checkbox('use_source_name', 'unreal', label='Use Source Name', position='left', checkerValue=False)
        self.create_or_show_checkbox('imp_static_mesh', 'unreal', label='Import Static Mesh', position='right', checkerValue=True)
        self.create_or_show_checkbox('imp_skeletal_mesh', 'unreal', label='Import Skeletal Mesh', position='right', checkerValue=True)

        imp_anim_id='imp_anim'
        unreal_anim_frame_id='unreal_anim_frame'
        self.create_or_show_checkbox(imp_anim_id, 'unreal', label='Import Animations', position='centerRight', checkerValue=False,
                                     onCommand=lambda arg:self.anim_build_state('unreal', imp_anim_id, 
                                                                                'imp_only_anims', state=True),
                                     offCommand=lambda arg:self.anim_build_state('unreal', imp_anim_id,
                                                                                 'imp_only_anims'))

        # build animation import configurations frame layout
        if mc.control(unreal_anim_frame_id, exists=True):
            mc.control(unreal_anim_frame_id, edit=True, vis=True)
        else:
            unreal_anim_frame = mc.frameLayout(unreal_anim_frame_id, parent=self.unreal_column, 
                                               label='Common Skeleton & Animation Configurations',
                                               collapsable=True, collapse=True,
                                               backgroundColor=(0.12,0.12,0.16), marginWidth=15,)
            self.frameLayouts[unreal_anim_frame_id] = unreal_anim_frame

            mc.columnLayout('imp_anim_column', parent=unreal_anim_frame, adj=True, generalSpacing=5.5,)

        # get skeleton data from current UE project
        # build skeleton selection menu
        skeletons = ['None']
        skeletons_data = self.get_ue_data('skeletons')
        if skeletons_data:
            for skeleton in skeletons_data:
                skeletons.append(skeleton)
        self.create_or_show_menu('skeleton', label='Select Skeleton:', layoutID='imp_anim_column',
                                 items=skeletons, separator=False, )

        self.create_or_show_checkbox('imp_meshes_bones', layoutID='imp_anim_column', label='Import Meshes in Bone Hierarchy', 
                                        checkerValue=False, separator=False)

        if mc.control('middle_separator_04', exists=True):
            mc.control('middle_separator_04', edit=True, visible=True)
        else:
            middle_separator_04 = mc.separator('middle_separator_04', style='none', 
                                            height=7.5, 
                                            parent=self.unreal_column)
            self.separators.append(middle_separator_04)

        # get root joint data from scene
        # build root joint selection menu
        jnts=['None', *md.get_root_jnts()]
        self.create_or_show_menu('root_jnts', label='Select Joint Root:', layoutID=self.unreal_column,
                                 items=jnts, separator=False)
        # set module function to select root joint in scene when changed
        mc.optionMenu('root_jnts', edit=True, 
                      cc=lambda arg:md.select_root_jnt(mc.optionMenu('root_jnts', query=True, value=True),
                                                       contains_list=True, jnts=jnts))

    def build_obj_ui_settings(self):
        ''' Handles the UI elements of the OBJ export and import settings. '''
        # re-enable exporter UI elements if they were disabled by clips UI
        mc.control(self.filename_field, edit=True, vis=True)
        mc.control('batch_export', edit=True, en=True)
        # build export settings checker objects
        self.create_or_show_checkbox('move_to_origin', 'maya', label='Move to Origin', position='left', checkerValue=True)
        self.create_or_show_checkbox('groups', 'maya', label='Groups', position='centerLeft', checkerValue=True)
        self.create_or_show_checkbox('pt_groups', 'maya', label='Point Groups', position='centerLeft', checkerValue=True)
        self.create_or_show_checkbox('materials', 'maya', label='Materials', position='centerRight', checkerValue=True)
        self.create_or_show_checkbox('smoothing', 'maya', label='Smoothing', position='right', checkerValue=True)
        self.create_or_show_checkbox('normals', 'maya', label='Normals', position='right', checkerValue=True)

        # build import settings checker objects
        self.create_or_show_checkbox('imp_materials', 'unreal', label='Include Materials', position='left', checkerValue=True)
        self.create_or_show_checkbox('imp_textures', 'unreal', label='Include Textures', position='centerLeft', checkerValue=False)
        self.create_or_show_checkbox('imp_static_mesh', 'unreal', label='Import Static Mesh', position='left', checkerValue=True)
        self.create_or_show_checkbox('imp_skeletal_mesh', 'unreal', label='Import Skeletal Mesh', position='centerLeft', checkerValue=True)
        self.create_or_show_checkbox('use_source_name', 'unreal', label='Import Asset with File Name', position='right', checkerValue=True)

    def create_or_show_checkbox(self, checkerID:str, layoutID:str, position:str|None=None, label:str="checkerName", 
                                checkerValue:bool=False, separator:bool=True, onCommand=None, offCommand=None):
        '''
        Builds a check box element. Requires string ID for check box callback and layout placement. 
        If the check box already exists, unhide and enable it alongside its separator.
        Position is only available when layoutID is set to 'maya' or 'unreal'. 
        If no on and off command functions is provided, switch_bool_state method will be set as default.
        '''
        # decide which frame and column inside the grid layout the check box will be placed
        if layoutID=='maya':
            if position == 'centerLeft':
                parentUI = self.centerLeft_maya_column
            elif position == 'centerRight':
                parentUI = self.centerRight_maya_column
            elif position == 'right':
                parentUI = self.right_maya_column
            else:
                parentUI = self.left_maya_column # default to left column
        elif layoutID=='unreal':
            if position == 'centerLeft':
                parentUI = self.centerLeft_unreal_column
            elif position == 'centerRight':
                parentUI = self.centerRight_unreal_column
            elif position == 'right':
                parentUI = self.right_unreal_column
            else:
                parentUI = self.left_unreal_column # default to left column
        else:
            # connect to unique layout ID
            parentUI = layoutID 

        # enable visibility of check box and separator if it has already been created
        if mc.control(checkerID, exists=True):
            mc.control(checkerID, edit=True, vis=True, en=True, parent=parentUI)
            if separator:
                mc.control(f'{checkerID}_separator', edit=True, vis=True, parent=parentUI)

        else:
            if not onCommand and not offCommand:
                onCommand=lambda arg:self.switch_bool_state(checkerID, state=True)
                offCommand=lambda arg:self.switch_bool_state(checkerID)

            # create the check box element
            mc.checkBox(checkerID, label=label,
                        parent=parentUI,
                        value=checkerValue,
                        onc=onCommand, ofc=offCommand)
        
            # connect checker identifier to it's boolean value for precise handling and callback
            self.checkerSettings[checkerID] = checkerValue

            if separator:
                # add vertical separator attached to checker column
                checker_separator = mc.separator(f'{checkerID}_separator', style='none', 
                                                    height=5, 
                                                    parent=parentUI)
                # store separator element information
                self.separators.append(checker_separator)
    
    def create_or_show_menu(self, menuID:str, layoutID:str, label:str="menuName", items:list=['Default Item'],
                           separator:bool=True, changeCommand=None):
        '''
        Builds a option menu element. Requires string ID for menu and item callback and layout placement. 
        If the menu already exists, unhide and enable it alongside its separator.
        Set layoutID to 'maya' or 'unreal' for frame layout placement. 
        Can set custom change command when provided.
        '''
        # decide which column the option menu will be placed
        if layoutID=='maya':
            parentUI = self.maya_column 
        elif layoutID=='unreal':
            parentUI = self.unreal_column
        else:
            parentUI = layoutID
        
        # enable visibility of option menu and separator if it has already been created
        if mc.control(menuID, exists=True):
            mc.control(menuID, edit=True, vis=True, en=True, parent=parentUI)
            if separator:
                mc.control(f'{menuID}_separator', edit=True, vis=True, parent=parentUI)

        else:
            menuElement=mc.optionMenu(menuID, label=label, parent=parentUI)
            if changeCommand:
                # attach custom change command when provided
                mc.optionMenu(menuElement, edit=True, cc=changeCommand)
            # create items for menu
            for item in items:
                mc.menuItem(item, label=item)

            # connect menu string identifier to it's UI element for precise callback
            self.menuSettings[menuID] = menuElement

            if separator:
                # add vertical separator attached to column
                menu_separator = mc.separator(f'{menuID}_separator', style='none',
                                              height=3, parent=parentUI)
                # store separator element information
                self.separators.append(menu_separator)

    def export_anim_state(self, state:bool=False):
        ''' Calls to build or unhide animation related UI elements depending on the export anim state. '''
        # activate import animation and enable its dependencies, if not already active 
        if state and not mc.checkBox('imp_anim', query=True, value=True):
            mc.checkBox('imp_anim', edit=True, value=True)
            self.checkerSettings['imp_anim']=True
            self.anim_build_state('unreal', 'imp_anim', 'imp_only_anims', state=True)

        # build bake anim checkbox and anim clips layout
        self.create_or_show_checkbox('bake_anim', self.maya_rowColumn, label='Bake Animation', checkerValue=False,
                                     separator=False)
        self.anim_build_state('maya', 'export_anim', 'maya_anim_frame', state=state)
        # show or hide bake anim checkbox element depending on state
        mc.control('bake_anim', edit=True, vis=state)

    def anim_build_state(self, section:str, checkerID:str, elementID:str, state:bool=False):
        ''' Builds or unhides animation related UI elements depending on the requested section. '''
        if section=='maya':
            # build layout with animation clips settings
            self.clipsUI.build_base_elements(parentUI=elementID)
            if self.clipsUI.get_clips_created():
                # hide filename and disable batch export when clips have been created
                mc.control(self.filename_field, edit=True, vis=False)
                mc.checkBox('batch_export', edit=True, en=False, value=False)

        elif section=='unreal':
            # build layout with import animations configurations 
            self.create_or_show_checkbox('imp_only_anims', layoutID='imp_anim_column', label='Import Only Animations', 
                                         checkerValue=False, separator=False)
            
        # show or hide the element depending on state
        mc.control(elementID, edit=True, vis=state)
        self.switch_bool_state(checkerID, state=state)

    def switch_bool_state(self, elementID:str, state:bool=False):
        ''' Changes boolean state of check box element: requires string identifier. '''
        self.checkerSettings[elementID]=state
        print(f"{elementID} set to: {self.checkerSettings[elementID]}")

    def disable_ui_elements(self):
        ''' Turns visibility and functionality off for stored UI elements.'''
        for frameLayout in self.frameLayouts:
            mc.control(frameLayout,
                       edit=True, vis=False)
        for checkerID in self.checkerSettings:
            if checkerID=='batch_export':
                continue
            mc.control(checkerID, 
                       edit=True, vis=False, en=False)
        for menuElement in self.menuSettings:
            mc.control(menuElement,
                       edit=True, vis=False, en=False)
        for separator in self.separators:
            mc.separator(separator,
                         edit=True, vis=False)
        
    def change_export_type(self, *args):
        ''' Handles switching UI elements depending on the requested exporter type. '''
        export_type = mc.optionMenu(self.exportType_menu, query=True, value=True)
        if export_type=='OBJ':
            mc.textFieldGrp(self.filename_field, edit=True, placeholderText='Name your .obj file')
            self.disable_ui_elements()
            
            self.build_obj_ui_settings()
            
            mc.button(self.export_button, edit=True, command=self.do_OBJ_export)
        
        elif export_type=='FBX':
            mc.textFieldGrp(self.filename_field, edit=True, placeholderText='Name your .fbx file')
            self.disable_ui_elements()

            self.build_fbx_ui_settings()
            
            mc.button(self.export_button, edit=True, command=self.do_FBX_export)

    def get_ue_data(self, dataID:str='path'):
        ''' Loads and returns UE project data. '''
        available_IDs = ['path', 'skeletons']
        if dataID not in available_IDs:
            mc.warning(f"Data ID: '{dataID}' not available. Available IDs: {available_IDs}")
        
        # verify UE project data exists
        ue_data_exists = md.path_exists(os.path.join(self.folder_path, 'ue_data.json'))
        # return None if no UE project data has been loaded, else return requested data
        if not ue_data_exists:
            return None
        else:
            ue_dict = md.load_data(self.folder_path, 'ue_data.json')
            if dataID=='path':
                ue_data = ue_dict.get("Current Project")
            elif dataID=='skeletons':
                ue_data = ue_dict.get("Skeletons")
                
            return ue_data

    def reload_ue_data(self, *args):
        ''' Retrieves the most recent UE project path and skeletons data. '''
        ue_path = self.get_ue_data()

        # clear previous skeleton menu items
        old_items=mc.optionMenu('skeleton', query=True, ill=True)
        for old_item in old_items:
            if 'None' not in old_item:
                mc.deleteUI(old_item)
        # warn user if no UE project data has been loaded
        if not ue_path:
            mc.warning('No UE project has been loaded! Make sure to load "unrealLoader.py" on UE project.')
            return
        else:
            self.print_UE_project_path()
            skeletons_data = self.get_ue_data('skeletons')
            if skeletons_data:
                # repopulate skeleton menu items
                for skeleton in skeletons_data:
                    mc.menuItem(label=skeleton, parent='skeleton')

    def print_UE_project_path(self):
        ''' Logs the currently active UE project path. '''
        # load project path data
        ue_project_path=self.get_ue_data()
        
        # print and write path to script editor and command line 
        sys.stdout.write(f"Current UE Project: {ue_project_path}\n")

    def do_FBX_export(self, *args):
        '''
        Handles the FBX export procedure. 
        Ensures no input error before executing exporter type methods.
        '''
        # load project path data
        ue_project_path = self.get_ue_data()
        # verify UE project path exists
        if not ue_project_path:
            mc.warning('No UE project has been loaded for export!')
            return
        
        # create a list of the selected mesh/es
        mesh_selection = mc.ls(selection = True)

        if not mesh_selection:
            mc.warning("Please select a mesh to export.")
            return
        
        # query the user's file & folder name
        mesh_file = mc.textFieldGrp(self.filename_field, query=True, text=True)
        folder_name = mc.textFieldGrp(self.foldername_field, query=True, text=True)

        # get animation clips data 
        clips_data = self.clipsUI.get_clips_created()
        # ensure file name is provided when no clips have been created
        if not clips_data:
            if not mesh_file:
                mc.warning('Please name your file for export.')
                return

        if folder_name:
            folder_name=folder_name.replace('\\', '/')
            # create a path inside the UE's project contents folder where the mesh will be exported to
            self.fbx.set_UE_project_path(ue_project_path, folder_name)
        else:
            mc.warning('Please provide a folder name to export.')
            return

        # store initial playback start & end frame range
        init_start_frame = mc.playbackOptions(query=True, minTime=True)
        init_end_frame = mc.playbackOptions(query=True, maxTime=True)

        # get move to origin bool value
        move_mesh = self.checkerSettings.get('move_to_origin')

        # evaluate user's fbx settings before exporting mesh 
        # evaluate if the mesh will be exported with Smoothing Groups information data
        self.fbx.export_smoothing_groups(self.checkerSettings.get('smooth_groups'))

        # evaluate if the mesh will be Subdivided once exported
        self.fbx.export_smooth_mesh(self.checkerSettings.get('smooth_mesh'))

        # evaluate if the mesh will contain Tangents & Binormals information data 
        self.fbx.export_tangents_binormals(self.checkerSettings.get('tangents'))

        # evaluate if the mesh will get Triangulated before exporting
        self.fbx.triangulate(self.checkerSettings.get('triangulate'))

        # evaluate if the mesh will be exported with Skin Deformation data
        self.fbx.export_skinWeights(self.checkerSettings.get('skins'))

        # evaluate if the mesh will contain geometry Blend Shapes from the current scene
        self.fbx.export_blendShapes(self.checkerSettings.get('blnd_shapes'))

        # evaluate if the mesh will be exported with Embedded Media (textures)
        self.fbx.export_embedded_textures(self.checkerSettings.get('embed_media'))

        # evaluate the primary axis the mesh will be exported with (Y-Up or Z-Up)
        axisValue = mc.optionMenu(self.menuSettings['axis'], query=True, value=True)
        if axisValue == 'Y-Up':
            self.fbx.up_axis(True)
        else:
            self.fbx.up_axis()

        # evaluate if the file will be exported as Ascii or Binary
        fbxFileType=mc.optionMenu(self.menuSettings['fileType'], query=True, value=True)
        if fbxFileType == "Ascii":
            self.fbx.file_type(True)
        else:
            self.fbx.file_type()

        # evaluate which FBX maya version will the mesh be exported in    
        fbxVersion = mc.optionMenu(self.menuSettings['version'], query=True, value=True)
        print(fbxVersion)
        self.fbx.file_version(fbxVersion)

        # get prefix and suffix text value
        prefix_name=mc.textFieldGrp(self.prefix_field, query=True, text=True)
        suffix_name=mc.textFieldGrp(self.suffix_field, query=True, text=True)

        # get batch export bool value
        batch_export=self.checkerSettings.get('batch_export')

        # check if import data has been generated prior
        import_data_exists = md.path_exists(os.path.join(self.folder_path, 'importSettings.json'))
        if import_data_exists:
            # load and store import settings data set
            import_data = md.load_data(self.folder_path, 'importSettings.json')
        else:
            # create empty import settings data set
            import_data = {}

        # clear data set; avoids conflict with latest version of importer script
        import_data.clear()
        # create fbx import settings data set
        fbx_import = {}
        import_data['FBX'] = fbx_import

        if self.checkerSettings.get('unused_jnts'):
            for mesh in mesh_selection:
                if mesh in md.get_root_jnts():
                    # get the root joints from selection and get their unused joints
                    jnts_data=md.get_unused_joints_in_hier([mesh])
                    if jnts_data:
                        # binds unused joints with 0 influence to skinned meshes before export
                        md.bind_unused_joints(jnts_data) # experimental; requires further testing

        if batch_export:
            iter_val=0
            for mesh in mesh_selection:
                main_name=mesh_file
                iter_val+=1
                mc.select(mesh)
                if move_mesh:
                    if mesh in md.get_root_jnts() or mc.nodeType(mesh) != 'joint':
                        self.fbx.move_sel_to_origin(mesh)

                # evaluate if animations will be exported
                if self.checkerSettings.get('export_anim'):
                    if self.checkerSettings.get('bake_anim'):
                        # bake every animation frame 
                        self.fbx.export_bake_anim(value=True)
                else:
                    # do export without animation
                    self.fbx.exclude_anim()

                file_name=self.set_export_file_name(mesh_file, extension='.fbx', keep_extension=False,
                                                    prefix=prefix_name, suffix=suffix_name)

                iter_file_name = main_name + f"_{iter_val}.fbx"

                import_settings=self.create_import_data(importer='FBX', skeleton_data=self.get_ue_data('skeletons'),) 
 
                # change & store file name and folder path values 
                fbx_import[iter_file_name]=import_settings
                import_settings['Folder Path']=folder_name

                self.fbx.set_file_name(iter_file_name)
                mc.select(mesh)
                self.fbx.export()

                if move_mesh:
                    # move mesh selection back to the original location prior to placing it at world origin
                    if mesh in md.get_root_jnts() or mc.nodeType(mesh) != 'joint':
                        self.fbx.place_sel_to_original_pos(mesh)

        else:
            if move_mesh:
                # move mesh selection to world origin [0,0,0]
                for mesh in mesh_selection:
                    if mesh in md.get_root_jnts() or mc.nodeType(mesh) != 'joint':
                        self.fbx.move_sel_to_origin(mesh)

            # evaluate if animations will be exported
            if self.checkerSettings.get('export_anim'):
                # check created clips and export each one as a separate file
                if clips_data:
                    for clip in clips_data:
                        clips_value=[]
                        # get values from each clip element and store them 
                        for clip_element in clips_data.get(clip):
                            if 'Add' in clip_element:
                                continue
                            elif 'Start' in clip_element:
                                clip_start=mc.intFieldGrp(clip_element, query=True, value1=True)
                                clips_value.append(clip_start)
                            elif 'End' in clip_element:
                                clip_end=mc.intFieldGrp(clip_element, query=True, value1=True)
                                clips_value.append(clip_end)
                            else:
                                clip_file_name=mc.textFieldGrp(clip_element, query=True, text=True)
                                if not clip_file_name:
                                    clips_value.append(None)
                                clips_value.append(clip_file_name)
                        if not clips_value[0]:
                            mc.warning('Please provide a file name for each animation clip.')
                            return
                        # set the animation range for export
                        if self.checkerSettings.get('bake_anim'):
                            self.fbx.export_bake_anim(value=True, start=clips_value[1], end=clips_value[2])

                        file_name=self.set_export_file_name(clips_value[0], extension='.fbx',
                                                            prefix=prefix_name, suffix=suffix_name)
                        import_settings=self.create_import_data(importer='FBX', animation_clips=[clips_value[1], clips_value[2]],
                                                                skeleton_data=self.get_ue_data('skeletons'),)
                        # change & store file name and folder path values 
                        fbx_import[file_name]=import_settings
                        import_settings['Folder Path']=folder_name

                        self.fbx.set_file_name(file_name)
                        mc.select(mesh_selection)
                        self.fbx.export()
                else:
                    # export animations without frame range
                    if self.checkerSettings.get('bake_anim'):
                        # bake every animation frame 
                        self.fbx.export_bake_anim(value=True)

                    file_name=self.set_export_file_name(mesh_file, extension='.fbx',
                                                        prefix=prefix_name, suffix=suffix_name)
                    import_settings=self.create_import_data(importer='FBX', skeleton_data=self.get_ue_data('skeletons'),)
                    # change & store file name and folder path values 
                    fbx_import[file_name]=import_settings
                    import_settings['Folder Path']=folder_name

                    self.fbx.set_file_name(file_name)
                    mc.select(mesh_selection)
                    self.fbx.export()

            else:
                # do export without animation
                self.fbx.exclude_anim()
                file_name=self.set_export_file_name(mesh_file, extension='.fbx',
                                                    prefix=prefix_name, suffix=suffix_name)
                        
                import_settings=self.create_import_data(importer='FBX', 
                                                        skeleton_data=self.get_ue_data('skeletons')) 
                # change & store file name and folder path values 
                fbx_import[file_name]=import_settings
                import_settings['Folder Path']=folder_name

                self.fbx.set_file_name(file_name)
                mc.select(mesh_selection)
                self.fbx.export()

            if move_mesh:
                # move mesh selection back to the original location prior placing it at world origin
                for mesh in mesh_selection:
                    if mesh in md.get_root_jnts() or mc.nodeType(mesh) != 'joint':
                        self.fbx.place_sel_to_original_pos(mesh)

        # save the user import settings for unreal importer
        md.save_data(self.folder_path, 'importSettings.json', import_data)

        # restore initial playback frame range
        mc.playbackOptions(edit=True, min=init_start_frame, max=init_end_frame)

        mc.select(cl=True)

    def do_OBJ_export(self, *args):
        '''
        Handles the OBJ export procedure. 
        Ensures no input error before executing exporter type methods.
        '''
        # load project path data
        ue_project_path = self.get_ue_data()
        # verify UE project path exists
        if not ue_project_path:
            mc.warning('No UE project has been loaded for export!')
            return

        # create a list of the selected mesh/es
        mesh_selection = mc.ls(selection = True)

        if not mesh_selection:
            mc.warning("Please select a mesh to export.")
            return
        
        # query the user's file & folder name
        mesh_file = mc.textFieldGrp(self.filename_field, query=True, text=True)
        folder_name = mc.textFieldGrp(self.foldername_field, query=True, text=True)

        if not mesh_file:
            mc.warning('Please name your file for export.')
            return

        if folder_name:
            folder_name=folder_name.replace('\\', '/')
            # create a path inside the UE's project contents folder where the mesh will be exported to
            self.obj.set_UE_project_path(ue_project_path, folder_name)
        else:
            mc.warning('Please provide a folder name to export.')
            return     

        move_mesh = self.checkerSettings['move_to_origin']

        # evaluate if mesh will contain group information data
        if self.checkerSettings['groups']:
            obj_groups=1
        
        # evaluate if mesh will contain point groups information data
        if self.checkerSettings['pt_groups']:
            obj_ptgroups=1

        # evaluate if mesh will contain material information data
        if self.checkerSettings['materials']:            
            obj_materials=1

        # evaluate if mesh will contain smoothing groups information data
        if self.checkerSettings['smoothing']:
            obj_smoothing=1

        # evaluate if mesh will contain normals information data
        if self.checkerSettings['normals']:
            obj_normals=1

        # check if import data has been generated prior
        import_data_exists = md.path_exists(os.path.join(self.folder_path, 
                                                              'importSettings.json'))
        if import_data_exists:
            # load and store import settings data set
            import_data = md.load_data(self.folder_path, 'importSettings.json')
        else:
            # create empty import settings data set
            import_data = {}

        # clear data set; avoids conflict with latest version of importer script
        import_data.clear()
        # create obj import settings data set
        obj_import = {}
        import_data['OBJ'] = obj_import

        # get prefix and suffix text value
        prefix_name=mc.textFieldGrp(self.prefix_field, query=True, text=True)
        suffix_name=mc.textFieldGrp(self.suffix_field, query=True, text=True)

        batch_export=self.checkerSettings['batch_export']

        if batch_export:
            iter_val=0
            for mesh in mesh_selection:
                iter_val+=1
                mc.select(mesh)
                # create temporary transform node 
                tempGrp=mc.group(empty=True)
                # parent mesh to transform node and rotate the node 90 degrees
                mc.parent(mesh, tempGrp)
                mc.rotate(90,0,0, tempGrp)

                if move_mesh:
                    # move mesh selection to world origin [0,0,0]
                    self.obj.move_sel_to_origin(mesh)

                file_name=self.set_export_file_name(mesh_file, extension='.obj', keep_extension=False,
                                                    prefix=prefix_name, suffix=suffix_name)

                iter_file_name = file_name + f"_{iter_val}.obj"
                self.obj.set_file_name(iter_file_name)
                import_settings=self.create_import_data()
                # change & store file name and folder path values 
                obj_import[iter_file_name]=import_settings
                import_settings['Folder Path']=folder_name

                # evaluate the user's settings and store them in a tuple for exporting
                self.obj.export(obj_groups, obj_ptgroups, obj_materials, 
                                obj_smoothing, obj_normals, 
                                include_textures=self.checkerSettings['imp_textures'])

                # undo rotation of temporary transform node
                mc.rotate(0,0,0, tempGrp)
                # unparent mesh to transform node and delete the node 
                mc.parent(mesh, world=True)
                mc.delete(tempGrp)

                if move_mesh:
                    # move mesh selection back to the original location prior placing it at world origin
                    self.obj.place_sel_to_original_pos(mesh)

        else: 
            # create temporary transform node 
            tempGrp=mc.group(empty=True)
            for mesh in mesh_selection:
                # parent mesh to transform node and rotate the node 90 degrees
                mc.parent(mesh, tempGrp)
            mc.rotate(90,0,0, tempGrp)

            if move_mesh:
            # move mesh selection to world origin [0,0,0]
                for mesh in mesh_selection:
                    self.obj.move_sel_to_origin(mesh)
            file_name=self.set_export_file_name(mesh_file, extension='.obj', 
                                                prefix=prefix_name, suffix=suffix_name)
            self.obj.set_file_name(file_name)

            import_settings=self.create_import_data()
            # change & store file name and folder path values 
            obj_import[file_name]=import_settings
            import_settings['Folder Path']=folder_name

            # evaluate the user's settings and store them in a tuple for exporting
            self.obj.export(obj_groups, obj_ptgroups, obj_materials, 
                            obj_smoothing, obj_normals, 
                            include_textures=self.checkerSettings['imp_textures'])
        
            # undo rotation of temporary transform node
            mc.rotate(0,0,0, tempGrp)
            for mesh in mesh_selection:
                # unparent mesh to transform node and delete the node 
                mc.parent(mesh, world=True)
            mc.delete(tempGrp)

            # move mesh selection back to the original location prior to placing it at world origin
            if move_mesh:
                for mesh in mesh_selection:
                    self.obj.place_sel_to_original_pos(mesh)

        # save the user import settings for unreal importer
        md.save_data(self.folder_path, 'importSettings.json', import_data)

        mc.select(cl=True)

    def set_export_file_name(self, file_name:str, prefix:str|None=None, suffix:str|None=None,
                             extension:str='.obj', keep_extension:bool=True):
        ''' 
        Builds and returns the export file name with optional prefix and suffix string values.
        Can only build with '.obj' or '.fbx' extensions.
        '''
        avilable_extensions = ['.obj', '.fbx']
        if extension not in avilable_extensions:
            mc.warning(f"Extension: '{extension}' not available. Available extensions: {avilable_extensions}")
            return file_name
        
        # concatenate prefix and/or prefix is value exists
        if prefix:
            file_name = prefix+file_name
        if extension in file_name:
            file_name = file_name.split(extension)[0]
        if suffix:
            file_name += suffix
        # if the user didn't add extension at the end of the file name, add it
        if keep_extension:
            if not file_name.endswith(extension):
                file_name += extension

        return file_name

    def create_import_data(self, importer:str='OBJ', animation_clips:list|None=None, 
                           skeleton_data:dict|None=None):
        ''' 
        Handles the configuration of the import settings data set.
        Defaults to OBJ importer unless otherwise specified.
        '''
        import_settings = {}
        
        # overwrite values with check box selection (user settings)
        import_settings['Import Materials']=self.checkerSettings.get('imp_materials')
        import_settings['Import Textures']=self.checkerSettings.get('imp_textures')
        import_settings['Import Static Mesh']=self.checkerSettings.get('imp_static_mesh')
        import_settings['Import Skeletal Mesh']=self.checkerSettings.get('imp_skeletal_mesh')
        import_settings['Use Source Name']=self.checkerSettings.get('use_source_name')

        # set FBX specific import settings
        if importer=='FBX':
            if import_settings['Import Static Mesh'] and not import_settings['Import Skeletal Mesh']:
                import_settings['Force Mesh Type']=1
            import_settings['Import Animations']=self.checkerSettings.get('imp_anim')
            if import_settings['Import Animations']:
                # set additional animation import settings 
                import_settings['Import Only Animations']=self.checkerSettings.get('imp_only_anims')
                # get animation clips frame range
                if animation_clips:
                    import_settings['Animation Range']=animation_clips
                else:
                    import_settings['Animation Range']=None

            # query and set skeleton asset from UE project skeletons data, if available
            skeleton = mc.optionMenu(self.menuSettings['skeleton'], query=True, value=True)
            if skeleton != 'None' and skeleton_data:
                skeleton_asset=f'{skeleton_data.get(skeleton)}.{skeleton}'
                import_settings['Skeleton']=skeleton_asset
            else:
                import_settings['Skeleton']=None
            import_settings['Meshes in Bone Hierarchy']=self.checkerSettings.get('imp_meshes_bones')

        return import_settings

        

