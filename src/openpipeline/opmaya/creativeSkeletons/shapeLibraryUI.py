from ..library import maya_utils as md, shape_saver as svr, shapes as shp
from .. import data_utils as dutil
from pathlib import Path
import maya.cmds as mc
import importlib
import os

# DELETE importlib reloads for public release
importlib.reload(md)
importlib.reload(shp)
importlib.reload(svr)

WINDOW_ID='ShapeLibraryUIWindow'
WINDOW_TITLE='creativeShapes v0.2'
ORIGINAL_WIDTH=400
ORIGINAL_HEIGHT=450

def show_shapeLibraryUI():
    shapeLibraryUI().show_mainWindow(deleteInstance=True)

class shapeLibraryUI:
    ''''
    Displays shapes that can be created for building control rigs.
    Can save selected shapes into the library; can create UE control rig shapes.
    '''
    window_size = (ORIGINAL_WIDTH, ORIGINAL_WIDTH)
    def __init__ (self):

        # store the directory path for icon file calls
        self.baseDirectory=Path(__file__).parents[1]
        # shape name label trackers
        self.selectedShapeLabel = None
        self.newShapeLabel = None # for newly saved/stored shapes
        self._customShapeList = [] # manager for new shape icons into the scroll ui  

    def build_window_layout(self):
        ''' Builds the main UI window layout for the shape library. '''
        self.windowDisplay = mc.window(WINDOW_ID, title=WINDOW_TITLE, widthHeight=self.window_size, sizeable=True)

        # create & set form layout with UI elements
        self.mainLayout = mc.formLayout(parent=self.windowDisplay)
        topLayout = mc.columnLayout(adjustableColumn=False, parent=self.mainLayout,
                                    rowSpacing=10)

        self.shapeFrameLayout = mc.frameLayout(borderVisible=True, labelVisible=False, parent=topLayout, 
                                               width=560, height=400, generalSpacing=20)
        shapeScroll = mc.scrollLayout(horizontalScrollBarThickness=0, parent=self.shapeFrameLayout)
        # place every selectable shape icon UI starting from the default circle and square 
        self.shapeGridLayout = mc.gridLayout(numberOfColumns=4, cellWidthHeight=[135,150], parent=shapeScroll)

        self.shapeRadioCollection = mc.iconTextRadioCollection('shapeRadioCollection', parent=self.shapeGridLayout)

        self.circleShape = mc.iconTextRadioButton(image1=os.path.join(self.baseDirectory, 'library',
                                                                      'imgs', 'Circle.jpg'), label='circle',
                                                                      style='iconAndTextVertical', onc=self.set_circle_shape, 
                                                   collection=self.shapeRadioCollection, parent=self.shapeGridLayout)
        self.squareShape = mc.iconTextRadioButton(image1=os.path.join(self.baseDirectory, 'library',
                                                                      'imgs', 'Square.jpg'), label='square',
                                                                      style='iconAndTextVertical', onc=self.set_square_shape, 
                                                   collection=self.shapeRadioCollection, parent=self.shapeGridLayout)
        self.update_shapes_ui()

        midLayout = mc.columnLayout(adjustableColumn=True, parent=self.mainLayout,
                                    rowSpacing=10)

        mc.button(label='Save a Selected Shape', parent=midLayout,
                  command=self.save_shape_ui)

        # create user input value settings
        prefixSuffixLayout=mc.rowColumnLayout('prefixSuffixLayout', numberOfColumns=2, parent=midLayout,
                                              columnWidth=[(1, 260), (2, 260)],
                                              columnAttach=[(1, 'right', 1), (2, 'left', 1)],
                                              columnAlign=[(1, 'right'), (2, 'left'), ])
        
        # create prefix and suffix fields
        self.prefixTextField=mc.textFieldGrp(label='Prefix:', parent=prefixSuffixLayout,
                                             columnWidth=[(1,50), (2,80)], enable=True) 
        self.suffixTextField=mc.textFieldGrp(label='Suffix:', text='_ctrl', parent=prefixSuffixLayout,
                                             columnWidth=[(1,50), (2,80)], enable=True)
        # create checkbox for adding zero/offset node groups on top of created shape
        zeroNodeLayout=mc.rowColumnLayout(parent=midLayout, columnAttach=(1, 'left', 180))
        mc.checkBox('zeroNodeCheck', label='Create with Zero/Offset Node', parent=zeroNodeLayout,
                    value=True)

        # create layout for controller creation options based onn joint selection
        ctrlLayout=mc.rowColumnLayout(numberOfColumns=2, parent=midLayout,
                                      columnAttach=[(1, 'left', 100), (2, 'left', 10)],
                                      columnAlign=[(1, 'right'), (2, 'left'), ])

        mc.checkBox('selectedJntsCheck', label='Create controllers for selected Joints', parent=ctrlLayout,
                    value=False, 
                    onc=lambda *args:self.swap_createShapes_dependencies(enableField=False),
                    ofc=lambda *args:self.swap_createShapes_dependencies())
        mc.checkBox('selectHierarchyCheck', label='Create with Hierarchy', parent=ctrlLayout,
                    value=False, enable=False)
        
        constraintsLayout=mc.rowColumnLayout('constraintsLayout', numberOfColumns=3, parent=midLayout,
                                             columnAttach=[(1, 'left', 80), (2, 'left', 15)],
                                             columnAlign=[(1, 'right'), (2, 'left'), (3, 'left')],
                                             visible=False)
        mc.radioButtonGrp('constraintTypeCheck', nrb=2, l1='Position only', l2='Position and Orient', parent=constraintsLayout,
                          select=2, visible=False)
        mc.checkBox('rotateCurveCheck', label='Rotate Controller Curve', parent=constraintsLayout,
                    value=True, visible=False)
        
        replaceNamesLayout=mc.rowColumnLayout('replaceNamesLayout', numberOfColumns=2, parent=midLayout,
                                              columnWidth=[(1, 275), (2, 220)], 
                                              columnAttach=[(1, 'left', 1), (2, 'left', 1)],
                                              columnAlign=[(1, 'right'), (2, 'left')],
                                              columnOffset=[(1, 'left', 20), (2, 'left', 10)],
                                              visible=False)
        self.searchNameField=mc.textFieldGrp('searchNameField', label='Strip Joint Name:', parent=replaceNamesLayout,
                                              placeholderText='Joint Name String', columnWidth=(2,110),
                                              text='jnt', visible=False)
        self.replaceNameField=mc.textFieldGrp('replaceNameField', label='Replace Ctrl Name:', parent=replaceNamesLayout,
                                              placeholderText='Ctrl Name String', columnWidth=[(1,55), (2,110)],
                                              text='ctrl', visible=False)

        self.nameTextField = mc.textFieldGrp(label='Name:', parent=midLayout,
                                             placeholderText='Name your controller shape', 
                                             columnWidth=[2, 280],)

        self.scaleValue = mc.intSliderGrp(label='Scale:', parent=midLayout, field=True,
                                          columnWidth=[(1,30), (2,80)], fieldMinValue=1, 
                                          fieldMaxValue=1000, minValue=1, maxValue=10, value=1)

        # create color selection menu with option swap to select from index palette or RGB/HSV values
        self.colorMenu = mc.optionMenu(parent=self.mainLayout,
                                       changeCommand=self.swap_colorUI)
        mc.menuItem(label='Index')
        mc.menuItem(label='RBG/HSV')

        # color selection (Can be selected by index palette or with RGB/HSV values)
        paletteColumn=mc.columnLayout(adjustableColumn=True, parent=self.mainLayout)
        paletteFrame=mc.frameLayout(labelVisible=0, height=160, 
                                    parent=paletteColumn, visible=True)

        # create color index (rgb) list
        colors = []
        excluded = [0,1,2,3,5,14,16,19]
        for i in range(0, 32):
            if i not in excluded:
                colour = mc.colorIndex(i, query=True)
                colors.append(colour)
        # create palettePort with maya's override colors
        # make grid of 8 columns and 3 rows to display color palette
        self.colorPalette=mc.palettePort(dim=(8, 3), topDown=True, parent=paletteFrame,
                                         height=100, width=50, visible=True)
        for i, colour in enumerate(colors):
            mc.palettePort(self.colorPalette, edit=True, rgbValue=(i, colour[0], colour[1], colour[2]))
        
        # create alternative color selection option UI
        self.colorRGBWidget = mc.colorInputWidgetGrp(label='Value:', parent=paletteFrame,
                                                     rgb=(1, 1, 0), columnWidth=[(1,45), (2,150)], visible=False)

        # create button for the main tool functionality
        self.createShapeBtn = mc.button(label='Create Shapes', parent=self.mainLayout,
                                        command=self.create_shapes)

        # align the display's layout
        mc.formLayout(self.mainLayout, edit=True, attachForm=[(topLayout,'right', 10), (topLayout, 'left', 10), 
                                                              (topLayout, 'top', 10),
                                                              (midLayout,'right', 10), (midLayout, 'left', 10),
                                                              (midLayout, 'top', 10), (self.colorMenu, 'left', 10),
                                                              (paletteColumn, 'right', 10), (paletteColumn, 'left', 10),
                                                              (self.createShapeBtn, 'right', 5), (self.createShapeBtn, 'left', 5),
                                                              (self.createShapeBtn, 'bottom', 5),],
                                                attachControl=[(midLayout, 'top', 5, topLayout),
                                                               (self.colorMenu, 'bottom', 5, paletteColumn),
                                                               (paletteColumn, 'bottom', 10, self.createShapeBtn)])
    
    def update_shapes_ui(self, *args):
        ''' Restarts the shape frame icon library (container) inside the main UI window. '''
        shapeData_path = os.path.join(self.baseDirectory, 'library', 'data', 'shapes_cv.json')
        print(shapeData_path)

        if not dutil.path_exists(shapeData_path):
            raise ValueError(f'No Shape Data found: {shapeData_path}')
        shapeData = dutil.load_data((os.path.join(self.baseDirectory, 'library', 'data')), 'shapes_cv.json')

        for i in self._customShapeList:
            mc.deleteUI(i, control=True)
        self._customShapeList.clear()

        # create a list comprehension to sort label names of each shape found in the shape data set, exclude base circle and square shapes
        custom_shapeLabels = [label for label in shapeData if label not in ('circle', 'square')]

        for shapeLabel in custom_shapeLabels:
            customShape = mc.iconTextRadioButton(image1=os.path.join(self.baseDirectory, 'library',
                                                                     'imgs', f'{shapeLabel}.jpg'), label=shapeLabel, 
                                                                     style='iconAndTextVertical', onc=self.set_custom_shape, 
                                                 collection=self.shapeRadioCollection, parent=self.shapeGridLayout)
            self.popup_menu(shapeLabel, customShape)
            self._customShapeList.append(customShape)
  
    def popup_menu(self, shapeLabel, parentUI):
        ''' Creates a popup menu (right mouse click) for showing update saved shape window. '''
        popMenu = mc.popupMenu(numberOfItems=3,parent=parentUI)
        mc.menuItem(label='Rename Shape Label', command=lambda arg: self.rename_label_ui(shapeLabel, parentUI))

    def rename_label_ui(self, shapeLabel:str, button:str):
        ''' Handles creation of UI window for renaming an icon label. '''
        windowID = 'RenameShapeUI'
        windowTitle = 'Flexible Shapes Library'
        size = (300,250)

        if mc.window(windowID, exists=True):
            mc.deleteUI(windowID, window=True)  

        windowUI = mc.window(windowID, title=windowTitle, widthHeight=size, sizeable=True)

        layoutUI = mc.formLayout(parent=windowUI)

        # build function window UI
        top_col = mc.columnLayout(adjustableColumn=True, rowSpacing=10)
        mc.text(label='Rename Shape', align='center')

        rename_shapeLabel = mc.textFieldGrp(label='Name:', placeholderText='Rename your shape for the library')

        mc.setParent('..')

        saveSHP_button = mc.button(label='Rename Shape', command=lambda arg: self.rename_label(shapeLabel, rename_shapeLabel, button))

        # align the button at the bottom of the window
        mc.formLayout(layoutUI, edit=True, attachForm=[(top_col, 'right', 5), (top_col, 'left', 5), (top_col, 'top', 5),
                                                       (saveSHP_button, 'right', 5), (saveSHP_button, 'left', 5), (saveSHP_button, 'bottom', 5),],
                                        attachControl=[(top_col, 'bottom', 5, saveSHP_button),])

        mc.showWindow()

    def rename_label(self, shapeLabel:str, renameField:str, button:str):
        ''' Changes the key (shape label) variable name for a shape stored in the JSON data. '''
        # get shapeData dictionary and get the key variables
        # store the values (data) of obtained key variable
        shapeData = dutil.load_data((os.path.join(self.baseDirectory, 'library', 'data')), 'shapesCV_Data.json')
        for shape in shapeData.keys():
            if shape==shapeLabel:
                print(f'Rename {shapeLabel}')
                cvData = shapeData.get(shapeLabel)

        newName = mc.textFieldGrp(renameField, query=True, text=True)
        if newName:
            print(cvData)
            print(newName)
            # update dictionary with new key variable that contains the same (previously obtained) data
            shapeData.update({newName:cvData})
            # remove the obtained/called key from dictionary
            shapeData.pop(shapeLabel)
            # remove icon button UI info from the shape library
            self._customShapeList.remove(button)
            # rename shape image thumbnail
            os.rename(os.path.join(self.baseDirectory, 'library','imgs', f'{shapeLabel}.jpg'), 
                      os.path.join(self.baseDirectory, 'library', 'imgs', f'{newName}.jpg'))
            # overwrite updated dictionary data on top of old JSON data
            dutil.save_data((os.path.join(self.baseDirectory, 'library', 'data')), 'shapesCV_Data.json', shapeData)
            # update icon button UI with new given name 
            updatedButton = mc.iconTextRadioButton(button, edit=True, image1=os.path.join(self.baseDirectory, 'library',
                                                                                          'imgs', f'{shapeLabel}.jpg'), 
                                                                                          label=shapeLabel)
            # add newly updated icon button UI info to shape library
            self._customShapeList.append(updatedButton)
            print(self._customShapeList)
            # update shape library frame UI
            self.update_shapes_ui()
        else:
            mc.warning('No name given to rename shape.')
            
    def save_shape_ui(self, *args):
        ''' Handles creation of UI window for saving selected shape settings into the current library. '''
        windowID = 'SAVESHAPE'
        windowTitle = 'Flexible Shapes Library'
        size = (400,250)

        if mc.window(windowID, exists=True):
            mc.deleteUI(windowID, window=True)  

        windowUI = mc.window(windowID, title=windowTitle, widthHeight=size, sizeable=True)

        layoutUI = mc.formLayout(parent=windowUI)

        top_col = mc.columnLayout(adjustableColumn=True, rowSpacing=10)
        mc.text(label='Set Save Settings:', align='center')

        self.newShapeLabel = mc.textFieldGrp(label='Set Shape Name:', placeholderText='Name the shape to store in the library')

        # store the saving shape settings
        self.saveSettingsGrp = mc.checkBoxGrp(label='Save Settings:', numberOfCheckBoxes=2, columnWidth=[(1, 140), (2, 140)],
                                               label1='Use Active Camera', value1=True,
                                               label2='Use Current Background', value2=False) 
        mc.setParent('..')

        saveSHP_button = mc.button(label='Save Selected Shape', command=self.save_shape)

        # align the button at the bottom of the window
        mc.formLayout(layoutUI, edit=True, attachForm=[(top_col, 'right', 5), (top_col, 'left', 5), (top_col, 'top', 5),
                                                       (saveSHP_button, 'right', 5), (saveSHP_button, 'left', 5), (saveSHP_button, 'bottom', 5),],
                                        attachControl=[(top_col, 'bottom', 5, saveSHP_button),])

        mc.showWindow()

    def save_shape(self, *args):
        ''' Helper method to save selected shape into the current library and updates the UI. '''
        custom_shapeLabel = mc.textFieldGrp(self.newShapeLabel, query=True, text=True)

        activeCam = mc.checkBoxGrp(self.saveSettingsGrp, query=True, value1=True)
        currentBG = mc.checkBoxGrp(self.saveSettingsGrp, query=True, value2=True)

        svr.save_selected_shape((os.path.join(self.baseDirectory, 'library', 'data')), 
                                (os.path.join(self.baseDirectory, 'library', 'imgs')), 
                                customLabel=custom_shapeLabel, activeCamera=activeCam, currentBG=currentBG)
        mc.deleteUI('SAVESHAPE')
        self.update_shapes_ui()

    def set_circle_shape(self, *args):
        self.selectedShapeLabel = mc.iconTextRadioButton(self.circleShape, query=True, label=True)

    def set_square_shape(self, *args):
        self.selectedShapeLabel = mc.iconTextRadioButton(self.squareShape, query=True, label=True)

    def set_custom_shape(self, *args):
        self.selected_shape = mc.iconTextRadioCollection(self.shapeRadioCollection, query=True, select=True)

        self.selectedShapeLabel = mc.iconTextRadioButton(self.selected_shape, query=True, label=True)
        
    def create_shapes(self, *args):
        ''' Creates shape based on UI selection, collects the input settings for naming, scaling, and coloring. '''
        if not self.selectedShapeLabel:
            mc.warning('Select a shape to create.')
            return
        
        shapeData = dutil.load_data((os.path.join(self.baseDirectory, 'library', 'data')), 'shapesCV_Data.json')

        # query the input settings for creation
        shapeName = mc.textFieldGrp(self.nameTextField, query=True, text=True)
        if not shapeName:
            mc.warning('Name your shape before creating.')
            return
        full_shapeName = shapeName

        prefix = mc.textFieldGrp(self.prefixTextField, query=True, text=True)
        if prefix:
            full_shapeName = prefix+shapeName

        suffix = mc.textFieldGrp(self.suffixTextField, query=True, text=True)
        if suffix: 
            full_shapeName += suffix

        ctrlSize = mc.intSliderGrp(self.scaleValue, query=True, value=True)

        colorValue = mc.optionMenu(self.colorMenu, query=True, value=True)
        if colorValue=='RBG/HSV':
            shapeColor = mc.colorInputWidgetGrp(self.colorRGBWidget, query=True, rgb=True)
            
        else:
            shapeColor = mc.palettePort(self.colorPalette, query=True, rgb=True) 

        if self.selectedShapeLabel == 'circle':
            ctrl=shp.circleShape(name=full_shapeName, radius=ctrlSize, typeOverride=shapeColor)

        elif self.selectedShapeLabel == 'square':
            ctrl=shp.customShape(shapeData, radius=ctrlSize, name=full_shapeName, typeOverride=shapeColor)

        else:
            ctrl=shp.customShape(shapeData, shapeLabel=self.selectedShapeLabel, 
                                 radius=ctrlSize, name=full_shapeName, typeOverride=shapeColor)

        if mc.checkBox('zeroNodeCheck', query=True, value=True):
            grpNode=mc.group(n=ctrl+'_zero', empty=True)
            mc.parent(ctrl, grpNode)
        
    def create_joint_controllers(self, *args):
        ''' Creates shapes based on UI selection for each selected joint, placing and orienting them based on the joint. '''
        if not self.selectedShapeLabel:
            mc.warning('Select a shape to create.')
            return

        jntSelection=mc.ls(selection=True, type='joint')
        if not jntSelection:
            mc.warning('Please select joints in order to create controllers.')
            return
        
        shapeData = dutil.load_data((os.path.join(self.baseDirectory, 'library', 'data')), 'shapesCV_Data.json')

        ctrlSize = mc.intSliderGrp(self.scaleValue, query=True, value=True)

        colorValue = mc.optionMenu(self.colorMenu, query=True, value=True)
        if colorValue=='RBG/HSV':
            shapeColor = mc.colorInputWidgetGrp(self.colorRGBWidget, query=True, rgb=True)
        else:
            shapeColor = mc.palettePort(self.colorPalette, query=True, rgb=True) 

        if mc.checkBox('selectHierarchyCheck', query=True, value=True):
            mc.select(jntSelection, hi=True)
            jntSelection=mc.ls(selection=True, type='joint')

        for jnt in jntSelection:
            replaceName=None
            searchName = mc.textFieldGrp(self.searchNameField, query=True, text=True)
            if searchName:
                replaceName = mc.textFieldGrp(self.replaceNameField, query=True, text=True)
                ctrlName=jnt.replace(searchName, replaceName)
            else:
                ctrlName=jnt+'_ctrl'

            childJoints = mc.listRelatives(jnt, c=True)
            if childJoints:
                if self.selectedShapeLabel == 'circle':
                    ctrl=shp.circleShape(name=ctrlName, radius=ctrlSize, typeOverride=shapeColor)
                elif self.selectedShapeLabel == 'square':
                    ctrl=shp.customShape(shapeData, name=ctrlName, radius=ctrlSize, typeOverride=shapeColor)
                else:
                    ctrl=shp.customShape(shapeData, name=ctrlName, shapeLabel=self.selectedShapeLabel,
                                        radius=ctrlSize, typeOverride=shapeColor)
                    
                print(ctrl)
                if mc.checkBox('rotateCurveCheck', query=True, value=True):
                    curveRot=md.get_curve_rotation(childJoints)

                    if curveRot != (0,0,0):
                        mc.rotate(curveRot[0], curveRot[1], curveRot[2], ctrl+'.cv[*]', os=True, relative=True)
                
                if mc.checkBox('zeroNodeCheck', query=True, value=True):
                    ctrlNode=ctrl+'_zero'
                    grpNode=mc.group(n=ctrlNode, empty=True)
                    mc.parent(ctrl, grpNode)
                else:
                    ctrlNode=ctrl

                mc.delete(mc.pointConstraint(jnt, ctrlNode))
                if mc.radioButtonGrp('constraintTypeCheck', query=True, select=2)==2:
                    print('Orient Controller')
                    mc.delete(mc.orientConstraint(jnt, ctrlNode))

    def swap_createShapes_dependencies(self, enableField=True):
        ''' Handles which UI elements, options and dependencies for shape creation are visible. '''
        if enableField:
            mc.control('prefixSuffixLayout', edit=True, visible=True)
            mc.control(self.prefixTextField, edit=True, visible=True)
            mc.control(self.suffixTextField, edit=True, visible=True)
            mc.control(self.nameTextField, edit=True, enable=True, visible=True)
            mc.control('selectHierarchyCheck', edit=True, enable=False)
            mc.control('constraintsLayout', edit=True, visible=False)
            mc.control('rotateCurveCheck', edit=True, visible=False)
            mc.control('constraintTypeCheck', edit=True, visible=False)
            mc.control('replaceNamesLayout', edit=True, visible=False)
            mc.control(self.searchNameField, edit=True, visible=False)
            mc.control(self.replaceNameField, edit=True, visible=False)

            mc.button(self.createShapeBtn, edit=True,
                      command=self.create_shapes)
        else:
            mc.control('prefixSuffixLayout', edit=True, visible=False)
            mc.control(self.prefixTextField, edit=True, visible=False)
            mc.control(self.suffixTextField, edit=True, visible=False)            
            mc.control(self.nameTextField, edit=True, enable=False, visible=False)
            mc.control('selectHierarchyCheck', edit=True, enable=True)
            mc.control('constraintsLayout', edit=True, visible=True)
            mc.control('rotateCurveCheck', edit=True, visible=True)
            mc.control('constraintTypeCheck', edit=True, visible=True)
            mc.control('replaceNamesLayout', edit=True, visible=True)
            mc.control(self.searchNameField, edit=True, visible=True)
            mc.control(self.replaceNameField, edit=True, visible=True)

            mc.button(self.createShapeBtn, edit=True, 
                      command=self.create_joint_controllers)

    def swap_colorUI(self, *args):
        colorValue = mc.optionMenu(self.colorMenu, query=True, value=True)
        if colorValue=='RBG/HSV':
            mc.palettePort(self.colorPalette, edit=True, visible=False)
            mc.colorInputWidgetGrp(self.colorRGBWidget, edit=True, visible=True)

        else:
            mc.palettePort(self.colorPalette, edit=True, visible=True)
            mc.colorInputWidgetGrp(self.colorRGBWidget, edit=True, visible=False)

    def show_mainWindow(self, deleteInstance=False):
        if deleteInstance:
            if mc.window(WINDOW_ID, exists=True):
                mc.deleteUI(WINDOW_ID, window=True)
        
        if not mc.window(WINDOW_ID, exists=True):
            self.build_window_layout()
            mc.showWindow(WINDOW_ID)
        else:
            mc.showWindow(WINDOW_ID)


            