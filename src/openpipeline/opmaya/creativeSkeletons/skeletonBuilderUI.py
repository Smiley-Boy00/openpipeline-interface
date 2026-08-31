from ..library import maya_utils as md
from ..wrapperQt import wrapperWidgets, wrapperLayouts
from PySide6 import QtCore, QtGui, QtWidgets
from shiboken6 import wrapInstance
from . import shapeLibraryUI as shpUI
import maya.api.OpenMaya as om2
import maya.OpenMayaUI as omui
import maya.cmds as mc
import os

# development only
import importlib
importlib.reload(md)
importlib.reload(wrapperWidgets)
importlib.reload(wrapperLayouts)

WINDOW_ID='skeletonBuilderUIWindow'
WINDOW_TITLE='creativeSkeletons v0.1'
ORIGINAL_WIDTH=405
ORIGINAL_HEIGHT=460

@QtCore.Slot()
def tester():
    print('This is a test')

def maya_main_window():
    mayaPtr=omui.MQtUtil.mainWindow()
    return wrapInstance(int(mayaPtr), QtWidgets.QWidget)

def show_skeletonBuilderUI_widget(dock:bool=False, workspaceName:str='CreativeSkeletonsWorkspace'):
    
    if dock: # WIP to allow window to be dockable, currently works but window & widgets don't get resized  
        if mc.workspaceControl(workspaceName, query=True, exists=True):
            mc.deleteUI(workspaceName)

        ctrl=mc.workspaceControl(workspaceName, label='Creative Skeletons',
                                    dockToMainWindow=('right', 1), retain=False)
        
        qtCrtl=wrapInstance(int(omui.MQtUtil.findControl(ctrl)), QtWidgets.QWidget)
        layout=qtCrtl.layout()
        if layout is None:
            layout = QtWidgets.QVBoxLayout(qtCrtl)
            layout.setContentsMargins(0,0,0,0)

        windowInstance=skeletonBuilderUI(parent=qtCrtl)
        layout.addWidget(windowInstance)
        return windowInstance
    else:
        mayaWindow=maya_main_window()
        # find any/all existing instances of the window & delete them
        outdatedWin=mayaWindow.findChildren(QtWidgets.QWidget, WINDOW_ID)
        if outdatedWin:
            for winToDel in outdatedWin:
                winToDel.setObjectName(f'outdated_{WINDOW_ID}')
                winToDel.close()
                winToDel.deleteLater()
        windowInstance=skeletonBuilderUI()
        windowInstance.setWindowFlag(QtCore.Qt.WindowType.Window)
        windowInstance.resize(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)
        windowInstance.show()
        return windowInstance

class skeletonBuilderUI(QtWidgets.QWidget):
    ''' Base Interface class to handle maya skeleton creation with UI elements. '''

    def __init__(self, parent=maya_main_window()):
        ''' Initialize the main window Display, set state alongside UI elements & dependencies. '''
        super(skeletonBuilderUI, self).__init__(parent)
        self.layouts=wrapperLayouts.wrapLay(self) # call layout wrapper instance
        self.widgets=wrapperWidgets.wrapWid(self) # call widget wrapper instance
        # store the directory path for icon file calls
        self.baseDirectory=os.path.dirname(__file__)

        self.setObjectName(WINDOW_ID)
        self.setWindowTitle(WINDOW_TITLE)

        # build vertical layout; attach to window display
        self.mainLayout=self.layouts.create_or_get_verticalLayout('mainLayout', spacing=5, contentMargins=(8,5,8,5))
        # build and set top icon buttons toolset
        self.build_top_buttons_layout()

        self.cardScrollArea = QtWidgets.QScrollArea()
        self.cardScrollArea.setWidgetResizable(True)
        self.cardScrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.cardScrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.cardScrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.mainLayout.addWidget(self.cardScrollArea)

        # build frame layout and look
        self.cardFrame=QtWidgets.QFrame()
        self.cardFrame.setObjectName('cardFrame')
        self.cardScrollArea.setWidget(self.cardFrame)
        self.cardLayout=self.layouts.create_or_get_verticalLayout('cardLayout', parentWidget=self.cardFrame, contentMargins=(5,5,5,5))

        # create tracking variables for locator joint creation, alongside layout display states
        self.sortedLocIDs=['none', 'none']
        self.sortedJntIDs=[] # stores joint ID strings in order of creation
        self.locatorSets={}
        self.locatorSetsCopy={} # copy needed for undo/redo operations; allows restoration of deleted locators
        self.locStartName=''
        self.locEndName=''
        self.jntLayoutDisplayed=False
        self.jntMidFields=[] # keeps instance of middle joint name fields for dynamic addition/removal

        # create static immutable ID values & parameters
        self.available_locatorIDs=['locator', 'cLocator'] # locator node types in case custom locators are unavailable
        self.available_sequenceID=['start', 'end']
        self.aimFieldID=['aimFieldX', 'aimFieldY', 'aimFieldZ']
        self.upFieldID=['upFieldX', 'upFieldY', 'upFieldZ']
        self.wupFieldID=['wupFieldX', 'wupFieldY', 'wupFieldZ']
        self.aimWidgetID=['aimCheck', 'aimBtn']

        self.build_main_layout()
        self._apply_style()

    def build_main_layout(self):
        ''' Handles the construction of the main UI layout structure and its elements. '''

        # build aim constraint checkbox & related fields
        aimForm=self.layouts.create_or_get_gridLayout('aimForm', parentWidget=self.cardFrame, parentLayout=self.cardLayout)
        aimForm.setAlignment(QtCore.Qt.AlignHCenter)
        self.mainLayout.addLayout(aimForm)
        self.widgets.create_checkbox(self.aimWidgetID[0], 'Locator Aim Constraint', aimForm, 
                                     clickedCmd=self.checkbox_aim_sequence)
        # initialize aim constraint related fields & buttons, hidden by default
        self.build_aim_layout()

        # build joint orientation & rotation order checkbox & related elements
        orientForm=self.layouts.create_or_get_gridLayout('orientForm', parentWidget=self.cardFrame, parentLayout=self.cardLayout)
        orientForm.setAlignment(QtCore.Qt.AlignHCenter)
        self.mainLayout.addLayout(orientForm)
        self.orientCheck=self.widgets.create_checkbox('orientCheck', 'Joint Orient | Rotation Order', orientForm,
                                     clickedCmd=self.checkbox_orient_sequence)
        self.build_orient_layout()

        # build joint chain mirroring checkbox & related elements
        mirrorCheckLayout=self.layouts.create_or_get_verticalLayout('mirrorCheckLayout', 
                                                                    parentWidget=self.cardFrame, parentLayout=self.cardLayout)
        mirrorCheckForm=self.layouts.create_or_get_gridLayout('mirrorCheckForm', parentLayout=mirrorCheckLayout)
        mirrorCheckForm.setAlignment(QtCore.Qt.AlignHCenter)
        mirrorJntsCheck=self.widgets.create_checkbox('mirrorJntsCheck', 'Mirror Joints', mirrorCheckForm,
                                                     clickedCmd=lambda *args:self.checkbox_mirror_sequence(mirrorJntsCheck.isChecked()))
        self.build_mirror_layout()

        self.locPrefixSuffixLabel=self.widgets.create_label('locPrefixSuffixLabel', 'Locator Prefix and Suffix names:',
                                                            self.cardLayout, align=QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter)
        # build fields to set the locator prefix and suffix names
        locPrefixSuffix=self.layouts.create_or_get_gridLayout('locPrefixSuffix', parentWidget=self.cardFrame, parentLayout=self.cardLayout,
                                                              contentMargins=(45,0,45,0))
        locPrefixSuffix.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter)
        self.locPrefixField=self.widgets.create_textField('locPrefixField', locPrefixSuffix,
                                                          placeholderText='Locator Prefix')
        self.locSuffixField=self.widgets.create_textField('locSuffixField', locPrefixSuffix, gridSet=(0,1),
                                                          placeholderText='Locator Suffix', text='_loc')
        
        locatorVLayout=self.layouts.create_or_get_verticalLayout('locatorVLayout', parentWidget=self.cardFrame,
                                                                 parentLayout=self.cardLayout, contentMargins=(30,3,30,3))
        self.locSizeField=self.widgets.create_numField('locSizeField', locatorVLayout, label='Locator Size Value:', type='float',
                                                    numVal=5, minVal=0.1, maxVal=100, align=QtCore.Qt.AlignHCenter)
        self.singleLocField=self.widgets.create_textField('singleLocField', locatorVLayout, placeholderText='Single Locator Name',
                                                          margins=(5,5,5,0))
        self.singleLocBtn=self.widgets.create_button('singleLocBtn', 'Create Single Locator', locatorVLayout,
                                   clickedCmd=self.create_single_locator)
        
        # create grid layout for main fields & buttons
        midLayout=self.layouts.create_or_get_gridLayout('midLayout', parentWidget=self.cardFrame, parentLayout=self.cardLayout)
        midLayout.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter)

        self.startLocCheck=self.widgets.create_checkbox('startLocCheck', 'Select Locator', midLayout, align=QtCore.Qt.AlignHCenter, 
                                                        clickedCmd=lambda args:self.checkbox_loc_sequence(self.startLocCheck.isChecked()))
        self.endLocCheck=self.widgets.create_checkbox('self.endLocCheck', 'Select Locator', midLayout, 
                                                      gridSet=(0,1), align=QtCore.Qt.AlignHCenter,
                                                      clickedCmd=lambda args:self.checkbox_loc_sequence(self.endLocCheck.isChecked(),
                                                                                                        sequenceID='end'))
        
        # build fields to set the locator names
        self.startLocField=self.widgets.create_textField('startLocField', midLayout, gridSet=(1,0),
                                                         placeholderText='Start Locator Name', margins=(5,0,5,0))
        self.endLocField=self.widgets.create_textField('endLocField', midLayout, gridSet=(1,1),
                                                       placeholderText='End Locator Name', margins=(5,0,5,0))

        # build buttons that handles the create or store locator modules 
        self.startLocBtn=self.widgets.create_button('startLocBtn', 'Create Start Locator', midLayout, gridSet=(2,0),
                                                    clickedCmd=lambda args:self.locator_btn_clicked())
        self.endLocBtn=self.widgets.create_button('endLocBtn', 'Create End Locator', midLayout, gridSet=(2,1),
                                                  clickedCmd=lambda args:self.locator_btn_clicked('end'))
        
        # create joint chain related layouts, fields & buttons, hidden by default
        parentConstLayout=self.layouts.create_or_get_gridLayout('parentConstLayout', parentWidget=self.cardFrame, parentLayout=self.cardLayout)
        parentConstLayout.setAlignment(QtCore.Qt.AlignHCenter)
        self.parentConstCheck=self.widgets.create_checkbox('parentConstCheck', 'Locator to Joint Constraint', 
                                                           parentConstLayout, visible=False)

        # create radio buttons to either set joint parenting methods or create joints without selection
        parentJntLayout=self.layouts.create_or_get_gridLayout('parentJntLayout', parentWidget=self.cardFrame, parentLayout=self.cardLayout)
        self.startParentCheck=self.widgets.create_radialButton('startParentCheck', 'Start from Selected Joint', 
                                                               parentJntLayout, enabled=False, visible=False,
                                                               align=QtCore.Qt.AlignHCenter)
        self.continueParentCheck=self.widgets.create_radialButton('continueParentCheck', 'Parent to Selected Joint',
                                                                  parentJntLayout, enabled=False, visible=False,
                                                                  align=QtCore.Qt.AlignHCenter, gridSet=(0,1))
        createJntLayout=self.layouts.create_or_get_gridLayout('createJntLayout', parentWidget=self.cardFrame, parentLayout=self.cardLayout)
        self.createJntCheck=self.widgets.create_radialButton('createJntCheck', 'Create Joint without Selection',
                                                             createJntLayout, enabled=False, visible=False, value=True,
                                                             align=QtCore.Qt.AlignHCenter)

        self.jntPrefixSuffixLabel=self.widgets.create_label('jntPrefixSuffixLabel', 'Joints Prefix and Suffix names:',
                                                            self.cardLayout, visible=False,
                                                            align=QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter)
        # build fields to set the joints prefix and suffix names
        jntPrefixSuffix=self.layouts.create_or_get_gridLayout('jntPrefixSuffix', parentWidget=self.cardFrame, parentLayout=self.cardLayout,
                                                              contentMargins=(45,0,45,0),)
        self.jntPrefixField=self.widgets.create_textField('jntPrefixField', jntPrefixSuffix,
                                                          placeholderText='Joints Prefix', visible=False)
        self.jntSuffixField=self.widgets.create_textField('jntSuffixField', jntPrefixSuffix, gridSet=(0,1),
                                                          placeholderText='Joints Suffix', text='_jnt',
                                                          visible=False)

        self.jntSizeField=self.widgets.create_numField('jntSizeField', self.cardLayout, label='Joint Radius Value:', type='float',
                                                       numVal=3, minVal=0.1, maxVal=100, align=QtCore.Qt.AlignHCenter,
                                                       visible=False)

        # build joint name fields layout
        jntNamesLayout=self.layouts.create_or_get_gridLayout('jntNamesLayout', parentWidget=self.cardFrame, parentLayout=self.cardLayout)
        self.jntStartField=self.widgets.create_textField('jntStartField', jntNamesLayout,
                                                         placeholderText='Starting Joint Name', visible=False)
        self.jntEndField=self.widgets.create_textField('jntEndField', jntNamesLayout, gridSet=(0,1),
                                                       placeholderText='Ending Joint Name', visible=False)
        # set connections to enable/disable starting joint name field based which radio button is selected
        self.startParentCheck.clicked.connect(lambda args:self.enable_jnt_nameField(False))
        self.continueParentCheck.clicked.connect(lambda args:self.enable_jnt_nameField(True))
        self.createJntCheck.clicked.connect(lambda args:self.enable_jnt_nameField(True))

        # build joint count layout with slider and numeric field (SpinBox)
        jntCountLayout=self.layouts.create_or_get_gridLayout('jntCountLayout', parentWidget=self.cardFrame, parentLayout=self.cardLayout)
        jntCountLayout.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter)
        countSliderWidth=300
        jntCountLayout.setColumnMinimumWidth(0, countSliderWidth)
        self.jntCountSlider=self.widgets.create_slider('jntCountSlider', jntCountLayout, QtCore.Qt.Horizontal,
                                                       align=QtCore.Qt.AlignHCenter, value=2, minVal=2,
                                                       visible=False, enabled=False, width=countSliderWidth)
        self.jntCountField=self.widgets.create_numField('jntCountField', jntCountLayout, gridSet=(0,1),
                                                        align=QtCore.Qt.AlignHCenter, numVal=2, minVal=2,
                                                        visible=False, enabled=False, width=60)
        # connect slider and spinbox numeric values together; reflect changes together
        self.jntCountSlider.valueChanged.connect(self.jntCountField.setValue)
        self.jntCountField.valueChanged.connect(self.jntCountSlider.setValue)
        self.jntCountField.valueChanged.connect(lambda *args: self.add_or_remove_jnt_nameFields(self.jntCountField.value()))

        # build button to handle the joint_chain module and reset UI
        self.jntBuilderBtn=self.widgets.create_button('jntBuilderBtn', 'Create Joint Chain', self.cardLayout, enabled=False,
                                                      clickedCmd=self.build_joint_chain)

        deleteBtnLayout=self.layouts.create_or_get_verticalLayout('deleteBtnLayout', parentWidget=self.cardFrame,
                                                                  parentLayout=self.cardLayout, contentMargins=(30,0,30,0))
        self.deleteConstBtn=self.widgets.create_button('deleteConstBtn', 'Delete Joint Constraints', deleteBtnLayout,
                                                       visible=False, clickedCmd=self.delete_jnt_constraints)
        self.commitBtn=self.widgets.create_button('commitBtn', 'Commit Joint Chain Structure', self.cardLayout, 
                                                  visible=False, clickedCmd=self.show_dialog_window)
        
        # build undo and redo buttons layout with their default state
        arrowLayout=self.layouts.create_or_get_gridLayout('arrowLayout', parentLayout=self.mainLayout)
        arrowLayout.setVerticalSpacing(10)
        arrowLayout.setAlignment(QtCore.Qt.AlignRight)
        arrowStyleSheet="""QToolButton {
                        border: 1px solid #555555;
                        border-radius: 3px;
                        background-color: #3a3a3a;
                        padding: 3px;}"""
        self.undoArrow=self.widgets.create_arrowButton('undoArrow', arrowLayout, direction='left',
                                        iconSize=QtCore.QSize(8, 8), styleSheet=arrowStyleSheet,
                                        enabled=False)
        self.redoArrow=self.widgets.create_arrowButton('redoArrow', arrowLayout, direction='right',
                                        iconSize=QtCore.QSize(8, 8), styleSheet=arrowStyleSheet,
                                        enabled=False, gridSet=(0,1))

        self.resize_layout(layout='card')

    def build_top_buttons_layout(self):
        ''' Handles the construction and display of the top right icon buttons. '''
        iconToolSetLayout=self.layouts.create_or_get_gridLayout('iconToolSetLayout', parentLayout=self.mainLayout)
        iconToolSetLayout.setHorizontalSpacing(2)
        iconToolSetLayout.setAlignment(QtCore.Qt.AlignRight)
        self.mainLayout.addLayout(iconToolSetLayout)
        iconBtnSizes=QtCore.QSize(24,24)

        lraIcon=QtGui.QIcon(os.path.join(self.baseDirectory, 
                                         'icons', 'menuIconDisplay_24.png'))
        lraBtn=QtWidgets.QToolButton()
        lraBtn.setIcon(lraIcon)
        lraBtn.setIconSize(iconBtnSizes)
        lraBtn.setAutoRaise(True)
        lraBtn.setFixedSize(24,24)
        lraBtn.clicked.connect(mc.ToggleLocalRotationAxes)

        selectHierIcon=QtGui.QIcon(os.path.join(self.baseDirectory , 
                                                'icons', 'menuIconSelect_24.png'))
        selectHierBtn=QtWidgets.QToolButton()
        selectHierBtn.setIcon(selectHierIcon)
        selectHierBtn.setIconSize(iconBtnSizes)
        selectHierBtn.setAutoRaise(True)
        selectHierBtn.setFixedSize(24,24)
        selectHierBtn.clicked.connect(mc.SelectHierarchy)

        selectHierLraIcon=QtGui.QIcon(os.path.join(self.baseDirectory, 
                                                   'icons', 'menuIconSelectDisplay_24.png'))
        selectHierLraBtn=QtWidgets.QToolButton()
        selectHierLraBtn.setIcon(selectHierLraIcon)
        selectHierLraBtn.setIconSize(iconBtnSizes)
        selectHierLraBtn.setAutoRaise(True)
        selectHierLraBtn.setFixedSize(24,24)
        selectHierLraBtn.clicked.connect(mc.SelectHierarchy)
        selectHierLraBtn.clicked.connect(mc.ToggleLocalRotationAxes)

        zeroJntRotIcon=QtGui.QIcon(':/FreezeTransform.png')
        zeroJntRotBtn=QtWidgets.QToolButton()
        zeroJntRotBtn.setIcon(zeroJntRotIcon)
        zeroJntRotBtn.setIconSize(iconBtnSizes)
        zeroJntRotBtn.setAutoRaise(True)
        zeroJntRotBtn.setFixedSize(24,24)
        zeroJntRotBtn.clicked.connect(mc.FreezeTransformations)

        shapeLibraryIcon=QtGui.QIcon(os.path.join(self.baseDirectory, 
                                                   'icons', 'shapeLibrary.png'))
        shapeLibraryBtn=QtWidgets.QToolButton()
        shapeLibraryBtn.setIcon(shapeLibraryIcon)
        shapeLibraryBtn.setIconSize(iconBtnSizes)
        shapeLibraryBtn.setAutoRaise(True)
        shapeLibraryBtn.setFixedSize(24,24)
        shapeLibraryBtn.clicked.connect(shpUI.show_shapeLibraryUI)

        iconToolSetLayout.addWidget(shapeLibraryBtn)
        iconToolSetLayout.addWidget(zeroJntRotBtn, 0, 1)
        iconToolSetLayout.addWidget(lraBtn, 0, 2)
        iconToolSetLayout.addWidget(selectHierBtn, 0, 3)
        iconToolSetLayout.addWidget(selectHierLraBtn, 0, 4)

    def build_aim_layout(self):
        ''' Handles the construction of the locator aim constraint layouts & related numeric fields. '''
        # build frame layout and look
        self.aimFrame=QtWidgets.QFrame()
        self.aimFrame.setObjectName('aimFrame')
        self.cardLayout.addWidget(self.aimFrame)
        aimFrameLayout=self.layouts.create_or_get_verticalLayout('aimFrameLayout', parentWidget=self.aimFrame, 
                                                                 contentMargins=(10,10,10,10))
        # create grid layout to place and align numeric fields
        vectorLayout=self.layouts.create_or_get_gridLayout('vectorLayout', parentWidget=self.aimFrame, 
                                                           parentLayout=aimFrameLayout)
        vectorLayout.setColumnMinimumWidth(0, 50)

        # create labels and numeric fields relating to each aim constraint parameters
        self.aimLabel=self.widgets.create_label('aimLabel', 'Aim Vector:', vectorLayout,
                                                visible=False, align=QtCore.Qt.AlignRight)
        self.widgets.create_numField(self.aimFieldID[0], vectorLayout, type='float',
                                     numVal=1, minVal=-10, visible=False, gridSet=(0,1))
        self.widgets.create_numField(self.aimFieldID[1], vectorLayout, type='float',
                                     minVal=-10, visible=False, gridSet=(0,2))
        self.widgets.create_numField(self.aimFieldID[2], vectorLayout, type='float',
                                     minVal=-10, visible=False, gridSet=(0,3))
        
        self.upLabel=self.widgets.create_label('upLabel', 'Up Vector:', vectorLayout,
                                               visible=False, align=QtCore.Qt.AlignRight,
                                               gridSet=(1,0))
        self.widgets.create_numField(self.upFieldID[0], vectorLayout, type='float',
                                     minVal=-10, visible=False, gridSet=(1,1))
        self.widgets.create_numField(self.upFieldID[1], vectorLayout, type='float',
                                     numVal=1, minVal=-10, visible=False, gridSet=(1,2))
        self.widgets.create_numField(self.upFieldID[2], vectorLayout, type='float',
                                     minVal=-10, visible=False, gridSet=(1,3))
        
        self.wupLabel=self.widgets.create_label('wupLabel', 'World Up Vector:', vectorLayout,
                                                visible=False, align=QtCore.Qt.AlignRight,
                                                gridSet=(2,0))
        self.widgets.create_numField(self.wupFieldID[0], vectorLayout, type='float',
                                     minVal=-10, visible=False, gridSet=(2,1))
        self.widgets.create_numField(self.wupFieldID[1], vectorLayout, type='float',
                                     numVal=1, minVal=-10, visible=False, gridSet=(2,2))
        self.widgets.create_numField(self.wupFieldID[2], vectorLayout, type='float',
                                     minVal=-10, visible=False, gridSet=(2,3))

        self.widgets.create_button(self.aimWidgetID[1], 'Set Aim Constraint', aimFrameLayout,
                                   visible=False, clickedCmd=self.aim_locators)
        self.aimFrame.setVisible(False)

    def build_orient_layout(self):
        ''' Handles the construction of the joint orientation and rotation order layouts & related elements. '''
        # build frame layout and look
        self.orientFrame=QtWidgets.QFrame()
        self.orientFrame.setObjectName('orientFrame')
        self.cardLayout.addWidget(self.orientFrame)
        orientFrameLayout=self.layouts.create_or_get_verticalLayout('orientFrameLayout', parentWidget=self.orientFrame, 
                                                                    contentMargins=(10,10,10,10))

        self.orientJntLabel=self.widgets.create_label('orientJntLabel', 'Joint Orientation & Secondary Axis:',
                                                      orientFrameLayout, visible=False,
                                                      align=QtCore.Qt.AlignHCenter)

        # create layout for joint orientation menus
        orientJntLayout=self.layouts.create_or_get_gridLayout('orientJntLayout', parentWidget=self.orientFrame, 
                                                              parentLayout=orientFrameLayout)

        # create joint orientation menus with their corresponding option items
        self.orientJntMenu=QtWidgets.QComboBox()
        self.orientJntMenu.setObjectName('orientJntMenu')
        self.orientJntMenu.addItems(['xyz', 'yzx', 'zxy', 'zyx', 'yxz', 'xzy', 'none'])
        self.orientJntMenu.hide()
        orientJntLayout.addWidget(self.orientJntMenu)

        self.secOrientMenu=QtWidgets.QComboBox()
        self.secOrientMenu.setObjectName('secOrientMenu')
        self.secOrientMenu.addItems(['xup', 'xdown', 'yup', 'ydown', 'zup', 'zdown', 'none'])
        self.secOrientMenu.hide()
        orientJntLayout.addWidget(self.secOrientMenu, 0, 1)

        # create joint orientation related checkboxes and button
        orientCheckLayout=self.layouts.create_or_get_gridLayout('orientCheckLayout', parentWidget=self.orientFrame, 
                                                                parentLayout=orientFrameLayout)
        self.orientChildCheck=self.widgets.create_checkbox('orientChildCheck', 'Orient Children',
                                                           orientCheckLayout, align=QtCore.Qt.AlignHCenter,
                                                           enabled=False, visible=False, value=True)

        self.orientWorldCheck=self.widgets.create_checkbox('orientWorldCheck', 'Orient to World',
                                     orientCheckLayout, align=QtCore.Qt.AlignHCenter,
                                     enabled=False, visible=False, gridSet=(1,0))
        
        self.orientBtn=self.widgets.create_button('orientBtn', 'Set Joint Orientation', orientFrameLayout,
                                                  enabled=False, visible=False,
                                                  clickedCmd=self.orient_bnt_clicked)

        self.rotOrderLabel=self.widgets.create_label('rotOrderLabel', 'Joint Rotation Order:',
                                  orientFrameLayout, visible=False,
                                  align=QtCore.Qt.AlignHCenter)

        # create joint rotation order menus with their corresponding option items
        rotOrderLayout=self.layouts.create_or_get_gridLayout('rotOrderLayout', parentWidget=self.orientFrame, 
                                                             parentLayout=orientFrameLayout)
        self.rotOrderMenu=QtWidgets.QComboBox()
        self.rotOrderMenu.setObjectName('rotOrderMenu')
        self.rotOrderMenu.addItems(['xyz', 'yzx', 'zxy', 'zyx', 'yxz', 'xzy'])
        self.rotOrderMenu.hide()
        rotOrderLayout.addWidget(self.rotOrderMenu)
        self.rotOrderBtn=self.widgets.create_button('rotOrderBtn', 'Set Joint Rotation Order', orientFrameLayout,
                                                    enabled=False, visible=False,
                                                    clickedCmd=self.joints_rotOrder)
        self.orientFrame.setVisible(False)

    def build_mirror_layout(self):
        ''' Handles the construction of the joint mirroring related elements. '''
        # build frame layout and look
        self.mirrorFrame=QtWidgets.QFrame()
        self.mirrorFrame.setObjectName('mirrorFrame')
        self.cardLayout.addWidget(self.mirrorFrame)
        mirrorFrameLayout=self.layouts.create_or_get_verticalLayout('mirrorFrameLayout', parentWidget=self.mirrorFrame, 
                                                                    contentMargins=(10,10,10,10))
        self.mirrorLabels=self.widgets.create_label('mirrorLabels', 'Mirror across | Mirror Function', mirrorFrameLayout,
                                                    visible=False, align=QtCore.Qt.AlignHCenter)
        mirrorMenuLayout=self.layouts.create_or_get_gridLayout('mirrorMenuLayout', parentWidget=self.mirrorFrame,
                                                               parentLayout=mirrorFrameLayout)

        self.mirrorAxisMenu=QtWidgets.QComboBox()
        self.mirrorAxisMenu.setObjectName('mirrorAxisMenu')
        self.mirrorAxisMenu.addItems(['YZ', 'XY', 'XZ'])
        self.mirrorAxisMenu.setVisible(False)
        mirrorMenuLayout.addWidget(self.mirrorAxisMenu)

        self.mirrorFuncMenu=QtWidgets.QComboBox()
        self.mirrorFuncMenu.setObjectName('mirrorFuncMenu')
        self.mirrorFuncMenu.addItems(['Behavior', 'Orientation'])
        self.mirrorFuncMenu.setVisible(False)
        mirrorMenuLayout.addWidget(self.mirrorFuncMenu, 0, 1)

        self.replaceLabel=self.widgets.create_label('replaceLabel', 'Replacement Names', mirrorFrameLayout,
                                                    visible=False, align=QtCore.Qt.AlignHCenter)

        mirrorFieldsLayout=self.layouts.create_or_get_gridLayout('mirrorFieldsLayout', parentWidget=self.mirrorFrame, 
                                                             parentLayout=mirrorFrameLayout)
        self.searchField=self.widgets.create_textField('searchField', mirrorFieldsLayout, 
                                                       label='Search for:', placeholderText='search',
                                                       visible=False)
        self.replaceField=self.widgets.create_textField('replaceField', mirrorFieldsLayout, gridSet=(0,1),
                                                        placeholderText='replace', label='Replace with:',
                                                        visible=False)

        transferCheckForm=QtWidgets.QFormLayout(self.mirrorFrame, formAlignment=QtCore.Qt.AlignHCenter)
        mirrorFrameLayout.addLayout(transferCheckForm)
        self.transferCheck=self.widgets.create_checkbox('transferCheck', 'Transfer Locators', transferCheckForm,
                                                        visible=False)

        self.mirrorJntsBtn=self.widgets.create_button('mirrorJntsBtn', 'Create Mirror Joints', mirrorFrameLayout,
                                                      visible=False, clickedCmd=self.mirror_joints)
        self.mirrorFrame.setVisible(False)

    def add_or_remove_jnt_nameFields(self, fieldAmount:int):
        ''' Handles the cyclical addition/removal of joint name fields based on a count value. '''
        jntNamesLayout=self.findChild(QtWidgets.QGridLayout, 'jntNamesLayout')
        midFields=fieldAmount-2 # there will always be 2 fields for start and end joints
        lastField=fieldAmount
        for field in self.jntMidFields:
            jntNamesLayout.removeWidget(field)
            field.deleteLater()

        self.jntMidFields.clear()

        for fieldNum in range(1, (midFields)+1):
            jntMidField=self.widgets.create_textField(f'jntMidField{fieldNum:02d}', jntNamesLayout,
                                                      placeholderText=f'Middle {fieldNum:02d} Joint Name',
                                                      gridSet=(0, fieldNum))
            lastField=fieldNum
            self.jntMidFields.append(jntMidField)
        
        # place end joint name field after the last middle joint name field
        jntNamesLayout.addWidget(self.jntEndField, 0, (lastField+1))    

    def show_or_hide_fields(self, fields='loc', hide=False):
        ''' Toggles the locator or joint prefix & suffix fields visibility. '''
        available_fields=['loc', 'jnt']
        if fields not in available_fields:
            raise ValueError(f'{fields} is not available field element, use: {available_fields}')
        # store fields prefix & suffix related fields & elements

        if hide:
            if fields=='loc':
                self.locPrefixSuffixLabel.setVisible(False)
                self.locPrefixField.setVisible(False)
                self.locSuffixField.setVisible(False)
                self.singleLocField.setVisible(False)
            else:
                self.jntPrefixSuffixLabel.setVisible(False)
                self.jntPrefixField.setVisible(False)
                self.jntSuffixField.setVisible(False)

        else:
            if fields=='loc':
                self.locPrefixSuffixLabel.setVisible(True)
                self.locPrefixField.setVisible(True)
                self.locSuffixField.setVisible(True)
                self.singleLocField.setVisible(True)
            else:
                self.jntPrefixSuffixLabel.setVisible(True)
                self.jntPrefixField.setVisible(True)
                self.jntSuffixField.setVisible(True)
        self.resize_layout(layout='card')

    def show_or_hide_joint_count(self, hideLayout=False, hideButton=False):
        ''' Toggles the joint count layout visibility, handles locator data reset. '''
        # find and store joint related fields, checkboxes & buttons
        jntSizeFieldForm=self.findChild(QtWidgets.QFormLayout, 'jntSizeFieldForm')
        
        if hideLayout:
            self.parentConstCheck.setVisible(False)
            self.parentConstCheck.setDisabled(True)
            self.startParentCheck.setVisible(False)
            self.startParentCheck.setDisabled(True)
            self.continueParentCheck.setVisible(False)
            self.continueParentCheck.setDisabled(True)
            self.createJntCheck.setVisible(False)
            self.createJntCheck.setDisabled(True)
            self.jntStartField.clear()
            self.jntStartField.setVisible(False)
            self.jntEndField.clear()
            self.jntEndField.setVisible(False)
            if self.jntMidFields:
                for jntMidField in self.jntMidFields:
                    jntMidField.clear()
                    jntMidField.setVisible(False)
            jntSizeFieldForm.setRowVisible(0, False)
            self.jntCountField.setVisible(False)
            self.jntCountField.setDisabled(True)
            self.jntCountSlider.setVisible(False)
            self.jntCountSlider.setDisabled(True)
            self.jntBuilderBtn.setDisabled(True)
            if hideButton:
                self.jntBuilderBtn.setVisible(False)
            self.show_or_hide_fields(fields='jnt', hide=True)

        else:
            self.parentConstCheck.setVisible(True)
            self.parentConstCheck.setEnabled(True)
            self.startParentCheck.setVisible(True)
            self.startParentCheck.setEnabled(True)
            self.continueParentCheck.setVisible(True)
            self.continueParentCheck.setEnabled(True)
            self.createJntCheck.setVisible(True)
            self.createJntCheck.setEnabled(True)
            self.jntStartField.setVisible(True)
            self.jntEndField.setVisible(True)
            if self.jntMidFields:
                for jntMidField in self.jntMidFields:
                    jntMidField.setVisible(True)
            jntSizeFieldForm.setRowVisible(0, True)
            self.jntCountField.setVisible(True)
            self.jntCountField.setEnabled(True)
            self.jntCountSlider.setVisible(True)
            self.jntCountSlider.setEnabled(True)
            self.jntBuilderBtn.setEnabled(True)
            self.show_or_hide_fields(fields='jnt')
            self.jntLayoutDisplayed=True

        self.resize_layout(layout='card')

    def show_or_hide_commitLayout(self, hide=False):
        ''' Toggles the commit button visibility. '''

        if hide:
            self.deleteConstBtn.setVisible(False)
            self.commitBtn.setVisible(False)
        else:
            self.deleteConstBtn.setVisible(True)
            self.commitBtn.setVisible(True)
        self.resize_layout(layout='card')

    def resize_layout(self, layout='main'):
        ''' Forces the main & secondary layout to recompute its original size based on visible elements. '''
        available_layouts=('main', 'card')
        if layout not in available_layouts:
            raise ValueError(f'{layout} is not an available layout, use: {available_layouts}')
        targetLayout=self.mainLayout if layout == 'main' else self.cardLayout

        targetLayout.invalidate()
        targetLayout.activate()

        # self.updateGeometry()
        self.adjustSize()
        self.resize(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)

    def delete_data(self):
        ''' Clears the locator and joint tracking properties. '''
        self.sortedLocIDs=['none', 'none']
        self.locatorSets.clear()
        self.sortedJntIDs.clear()

    def locator_btn_clicked(self, sequenceID:str='start'):
        ''' Handles the create or store locator methods based on checkbox state. '''
        if sequenceID not in self.available_sequenceID:
            raise ValueError(f'[{sequenceID}] is not an available sequence, use: [{self.available_sequenceID}]')

        # determine which locator sequence to process (start or end)
        # call the locator method based on checkbox state
        if sequenceID=='start':
            if self.startLocCheck.isChecked():
                self.stage_store_locator(self.startLocBtn, self.startLocField, self.startLocCheck)
            else:
                self.stage_build_locator(self.startLocBtn, self.startLocField, self.startLocCheck)  
            
        else:
            if self.endLocCheck.isChecked():
                self.stage_store_locator(self.endLocBtn, self.endLocField, self.endLocCheck,
                                         sequenceID='end')
            else:
                self.stage_build_locator(self.endLocBtn, self.endLocField, self.endLocCheck,
                                         sequenceID='end')

    def arrow_btn_clicked(self, arrowID:str, 
                          locBtn:QtWidgets.QPushButton,
                          locField:QtWidgets.QLineEdit,
                          locCheck:QtWidgets.QCheckBox,
                          locObjID, deleteLoc:bool=False,
                          text='Start'):
        ''' 
        Handles the undo and redo operations for locator creation and storage. 
        Parameters are passed to re-enable/disable the locator layout accordingly.
        Undo & Redo signals should be disconnected prior to connecting this method.
        '''

        if arrowID=='undo':
            if deleteLoc:
                # store a copy of the current locator sets, remove the deleted locator from the copy
                self.locatorSetsCopy=self.locatorSets.copy()
                self.locatorSetsCopy.pop(locObjID)

                mc.undo() # undoes the locator creation set by stage_build_locator method
                self.enable_locBtn(locBtn, locField, locCheck, buttonText=f'Create {text} Locator',
                                   clearField=False)
            else:
                # re-enable locator button, field & checkbox; no locator deletion
                self.enable_locBtn(locBtn, locField, locCheck, buttonText=f'Store {text} Locator',
                                   enableField=False, checkState=True)
            self.redoArrow.setEnabled(True)
            self.undoArrow.setDisabled(True)
            # verify if joint chain layout is displayed to hide it again
            if self.jntLayoutDisplayed:
                self.show_or_hide_joint_count(hideLayout=True)
                self.show_or_hide_fields() 
                self.jntLayoutDisplayed=False

        elif arrowID=='redo':
            # get locator position data from original locator sets, place the set back into the copy
            locObjPos=self.locatorSets.get(locObjID)
            self.locatorSetsCopy[locObjID]=locObjPos

            # redo the locator creation; if maya has reached the end of its redo stack simply skip to disable UI 
            try:
                mc.redo()
            except(RuntimeError):
                pass

            # disable locator button, field & checkbox again
            self.disable_locBtn(locBtn, locField, locCheck, locObjID)
            self.undoArrow.setEnabled(True)
            self.redoArrow.setDisabled(True)
            # check if both locator buttons have been disabled to enable joint chain layout
            self.check_locator_btns_disabled()

    def enable_locBtn(self, locBtn:QtWidgets.QPushButton, 
                      locField:QtWidgets.QLineEdit,
                      locCheck:QtWidgets.QCheckBox,
                      buttonText:str,
                      clearField:bool=True, 
                      enableField:bool=True,
                      checkState:bool=False):
        ''' Re-enables locator button, field & checkbox with optional parameters. '''
        locBtn.setEnabled(True)
        locBtn.setText(buttonText)
        locField.setEnabled(enableField)
        if clearField:
            locField.clear()
        locCheck.setEnabled(True)
        locCheck.setChecked(checkState)

    def disable_locBtn(self, locBtn:QtWidgets.QPushButton,
                       locField:QtWidgets.QLineEdit,
                       locCheck:QtWidgets.QCheckBox,
                       fieldText=None):
        ''' 
        Disables locator button, field & checkbox, can set new text. 
        Used to indicate that locator has been created/stored.
        '''
        locBtn.setDisabled(True)
        locCheck.setDisabled(True)
        locField.setDisabled(True)
        if fieldText:
            locField.setText(fieldText)

    def check_locator_btns_disabled(self):
        ''' 
        Checks if both locator buttons are disabled to enable and show the joint chain layout. 
        If aim constraint is checked, set up aim constraint between locators.
        '''

        if not self.startLocBtn.isEnabled() and not self.endLocBtn.isEnabled():
            if self.findChild(QtWidgets.QCheckBox, self.aimWidgetID[0]).isChecked():
                self.aim_locators()
            self.show_or_hide_joint_count()
            self.show_or_hide_fields(hide=True)
            self.findChild(QtWidgets.QFormLayout, 'locSizeFieldForm').setRowVisible(0, False)
            self.singleLocBtn.setVisible(False)
            self.resize_layout(layout='card')

    def checkbox_loc_sequence(self, checked:bool, sequenceID:str='start'):
        ''' Switches the information displayed for each locator layout: create or select locator. '''
        if sequenceID not in self.available_sequenceID:
            raise ValueError(f'[{sequenceID}] is not an available sequence, use: [{self.available_sequenceID}]')
        
        # determine which locator sequence to process (start or end)
        # enable/disable fields and change button text based on checkbox state
        if checked:
            if sequenceID=='start':
                self.locStartName=self.startLocField.text() # store name value in case user decides to uncheck selection option
                self.startLocField.setDisabled(True) 
                self.startLocField.clear()
                self.startLocField.setPlaceholderText('Select Start Locator')
                self.startLocBtn.setText('Store Start Locator')
            else:
                self.locEndName=self.endLocField.text() # store name value in case user decides to uncheck selection option
                self.endLocField.setDisabled(True)
                self.endLocField.clear() 
                self.endLocField.setPlaceholderText('Select End Locator')
                self.endLocBtn.setText('Store End Locator') 
        else:
            if sequenceID=='start':
                self.startLocField.setEnabled(True)
                self.startLocField.setText(self.locStartName) # restore previous name value
                self.startLocField.setPlaceholderText('Start Locator Name')
                self.startLocBtn.setText('Create Start Locator')
            else:
                self.endLocField.setEnabled(True)
                self.endLocField.setText(self.locEndName) # restore previous name value
                self.endLocField.setPlaceholderText('End Locator Name')
                self.endLocBtn.setText('Create End Locator')

    def checkbox_aim_sequence(self, checked:bool):
        ''' Shows or hides the aim constraint numeric fields based on checkbox state. '''
        # store all aim constraint related field IDs and label objects in a single list
        fieldIDs=[*self.aimFieldID, *self.upFieldID, *self.wupFieldID]
        # store label objects for easy visibility toggling
        labelObjs=[self.aimLabel, self.upLabel, self.wupLabel]
        if checked:
            # show and enable aim constraint layout elements
            self.aimFrame.setVisible(True)
            for label in labelObjs:
                label.setVisible(True)
            for field in fieldIDs:
                self.findChild(QtWidgets.QDoubleSpinBox, field).setVisible(True)
            self.findChild(QtWidgets.QPushButton, self.aimWidgetID[1]).setVisible(True)
        else:
            # hide and disable aim constraint layout elements, recompute main layout size
            self.aimFrame.setVisible(False)
            for label in labelObjs:
                label.setVisible(False)
            for field in fieldIDs:
                self.findChild(QtWidgets.QDoubleSpinBox, field).setVisible(False)
                self.findChild(QtWidgets.QDoubleSpinBox, field).setDisabled(True)
            self.findChild(QtWidgets.QPushButton, self.aimWidgetID[1]).setVisible(False)
        self.resize_layout(layout='card')

    def checkbox_orient_sequence(self, checked:bool):
        ''' Shows or hides the joint orientation & rotation order menus based on checkbox state. '''
        # find and store joint orientation related layout & its child widgets

        if checked:
            self.orientFrame.setVisible(True)

            self.orientJntLabel.setVisible(True)
            self.orientChildCheck.setVisible(True)
            self.orientChildCheck.setEnabled(True)
            self.orientWorldCheck.setVisible(True)
            self.orientWorldCheck.setEnabled(True)

            self.orientJntMenu.setVisible(True)
            self.secOrientMenu.setVisible(True)
            self.orientBtn.setVisible(True)
            self.orientBtn.setEnabled(True)
            self.rotOrderLabel.setVisible(True)
            self.rotOrderMenu.setVisible(True)
            self.rotOrderBtn.setVisible(True)
            self.rotOrderBtn.setEnabled(True)
        else:
            self.orientFrame.setVisible(False)

            self.orientJntLabel.setVisible(False)
            self.orientChildCheck.setVisible(False)
            self.orientChildCheck.setDisabled(True)
            self.orientWorldCheck.setVisible(False)
            self.orientWorldCheck.setDisabled(True)

            self.orientJntMenu.setVisible(False)
            self.secOrientMenu.setVisible(False)
            self.orientBtn.setVisible(False)
            self.orientBtn.setDisabled(True)
            self.rotOrderLabel.setVisible(False)
            self.rotOrderMenu.setVisible(False)
            self.rotOrderBtn.setVisible(False)
            self.rotOrderBtn.setDisabled(True)

        self.resize_layout(layout='card')

    def checkbox_mirror_sequence(self, checked:bool):
        ''' Shows or hides the joint mirroring related fields based on checkbox state. '''
        replaceFieldForm=self.findChild(QtWidgets.QFormLayout, 'replaceFieldForm')
        searchFieldForm=self.findChild(QtWidgets.QFormLayout, 'searchFieldForm')

        if checked:
            self.mirrorFrame.setVisible(True)

            self.mirrorLabels.setVisible(True)
            self.mirrorAxisMenu.setVisible(True)
            self.mirrorFuncMenu.setVisible(True)
            self.replaceLabel.setVisible(True)
            searchFieldForm.setRowVisible(0, True)
            replaceFieldForm.setRowVisible(0, True)
            self.transferCheck.setVisible(True)
            self.mirrorJntsBtn.setVisible(True)
        else:
            self.mirrorFrame.setVisible(False)

            self.mirrorLabels.setVisible(False)
            self.mirrorAxisMenu.setVisible(False)
            self.mirrorFuncMenu.setVisible(False)
            self.replaceLabel.setVisible(False)
            searchFieldForm.setRowVisible(0, False)
            replaceFieldForm.setRowVisible(0, False)
            self.transferCheck.setVisible(False)
            self.mirrorJntsBtn.setVisible(False)

        self.resize_layout(layout='card')

    def enable_jnt_nameField(self, value:bool=True):
        ''' Enables or disables the starting joint name field based on bool value for radio buttons. '''
        if value:
            self.jntStartField.setPlaceholderText('Starting Joint Name')
            self.jntStartField.setEnabled(True)
        else:
            self.jntStartField.setPlaceholderText('Select Starting Joint')
            self.jntStartField.setDisabled(True)

    def create_place_locator(self, locName:str, 
                             prefix:str|None=None, suffix:str|None=None, 
                             locScale:float=5):
        ''' Handles the create_locator & constrain_locator_to_cluster calls for either single or staged locator placement. '''
        locObjPos=mc.polyListComponentConversion(mc.ls(selection=True), toVertex=True)
        locObjID=md.create_locator(locName, prefix=prefix, suffix=suffix, locScale=locScale)
        if locObjPos:
            md.constrain_locator_to_cluster(locObjPos, locName, locObjID)
        return (locObjID, locObjPos)

    def create_single_locator(self):
        ''' Connected to singleLocBtn. Queries all the values to call create_place_locator. '''
        locName=self.singleLocField.text()
        if not locName:
            mc.warning('Please add a name for your Locator.')
            return
        locScale=self.locSizeField.value()
        locPrefix=self.locPrefixField.text()
        locSuffix=self.locSuffixField.text()
        locObjID=self.create_place_locator(locName, prefix=locPrefix, suffix=locSuffix, locScale=locScale)
        # if not locObjID:
        #     mc.warning('No Selection made.')
        #     return
        self.singleLocField.clear()
        print(f'{locObjID} created.')

    def stage_build_locator(self, locBtn:QtWidgets.QPushButton, 
                         locField:QtWidgets.QLineEdit,
                         locCheck:QtWidgets.QCheckBox,
                         sequenceID='start'):
        ''' 
        Handles the buildLocator module to create a locator on the user's selection (mesh, faces, edges or vertices). 
        If a locObjID is passed, finds it's stored position and rebuilds the locator.
        Disables the locator button, field & checkbox upon creation.
        '''
        if sequenceID not in self.available_sequenceID:
            raise ValueError(f'[{sequenceID}] is not an available sequence, use: [{self.available_sequenceID}]')
        # open undo chunk for locator creation
        mc.undoInfo(openChunk=True, chunkName="skeletonBuilderUI: stage_build_locator")
        try:
            print('Build Locator')
            mc.selectPriority(locator=2, polymesh=1) # set selection priority to locator over mesh

            # create a new locator from selection with user error handling
            locatorName=locField.text()
            if not locatorName:
                mc.warning('Please add a name for your Locator.')
                return
            locScale=self.locSizeField.value()
            locObj=self.create_place_locator(locatorName, prefix=self.locPrefixField.text(),
                                             suffix=self.locSuffixField.text(), locScale=locScale)
            if not locObj:
                mc.warning('No Selection made.')
                return
            locObjID, locObjPos = locObj[0], locObj[1] 

            # store locator ID based on the sequence provided 
            if sequenceID=='start':
                self.sortedLocIDs[0]=locObjID
                textID='Start'
            else:
                self.sortedLocIDs[1]=locObjID
                textID='End'
            # store locator ID and position data set for undo/redo operations
            self.locatorSets[locObjID]=locObjPos
            # set locator field text to show created locator ID
            locField.setText(locObjID)
            self.disable_locBtn(locBtn, locField, locCheck)

            # check if both locator buttons are disabled to enable joint chain layout
            self.check_locator_btns_disabled()

            # undo and redo arrow button connections; avoids ghost stacking
            self.undoArrow, self.redoArrow = self._reset_arrow_connections()
            self.undoArrow.setEnabled(True)
            self.redoArrow.setDisabled(True)

            # connect arrow buttons to handle undo/redo operations
            self.undoArrow.clicked.connect(lambda args:self.arrow_btn_clicked('undo',
                                                                        locBtn,
                                                                        locField,
                                                                        locCheck,
                                                                        locObjID, text=textID,
                                                                        deleteLoc=True))
            self.redoArrow.clicked.connect(lambda args:self.arrow_btn_clicked('redo',
                                                                         locBtn,
                                                                         locField,
                                                                         locCheck,
                                                                         locObjID, text=textID))

        finally:
            # close undo chunk for maya stack
            mc.undoInfo(closeChunk=True)

    def stage_store_locator(self, locBtn:QtWidgets.QPushButton, 
                      locField:QtWidgets.QLineEdit,
                      locCheck:QtWidgets.QCheckBox,
                      locObjID=None,
                      sequenceID='start'):
        ''' 
        Handles the storeLocator module to store an existing locator as the user's selection.
        If a locObjID is passed, uses that locator ID instead of the user's selection.
        Disables the locator button, field & checkbox upon storage.
        '''

        if not locObjID:
            # get user's selection and validate that it is a locator
            locSelection=mc.ls(selection=True)
            if not locSelection:
                mc.warning('Please select your locator.')
                return

            if len(locSelection)>1:
                mc.warning('Selection must be only one locator.')
                return
                
            locType=mc.nodeType(mc.listRelatives(locSelection[0], s=True)[0])
            if locType not in self.available_locatorIDs:
                mc.warning('Selection must be of type: locator.')
                return
            locObjID=locSelection[0]

        # store locator ID based on the sequence provided 
        if sequenceID=='start':
            self.sortedLocIDs[0]=locObjID
            textID='Start'
        else:
            self.sortedLocIDs[1]=locObjID
            textID='End'
        # stored locators don't require position data; position data is only needed for created locators
        self.locatorSets[locObjID]=None
        # set locator field text to show stored locator ID
        locField.setText(locObjID)
        self.disable_locBtn(locBtn, locField, locCheck)

        # check if both locator buttons are disabled to enable joint chain layout
        self.check_locator_btns_disabled()

        # undo and redo arrow button connections; avoids ghost stacking
        self.undoArrow, self.redoArrow = self._reset_arrow_connections()
        self.undoArrow.setEnabled(True)
        self.redoArrow.setDisabled(True)

        # connect arrow buttons to handle undo/redo operations
        self.undoArrow.clicked.connect(lambda args:self.arrow_btn_clicked('undo',
                                                                    locBtn,
                                                                    locField,
                                                                    locCheck, 
                                                                    locObjID, text=textID))
        self.redoArrow.clicked.connect(lambda args:self.arrow_btn_clicked('redo',
                                                                    locBtn,
                                                                    locField,
                                                                    locCheck,
                                                                    locObjID, text=textID))
        mc.select(clear=True)

    def aim_locators(self):
        ''' Sets up an aim constraint between two locators based on aim constraint numeric fields. '''
        
        # store value set for corresponding aim constraint flag
        aimVector=[self.findChild(QtWidgets.QDoubleSpinBox, self.aimFieldID[0]).value(),
                   self.findChild(QtWidgets.QDoubleSpinBox, self.aimFieldID[1]).value(),
                   self.findChild(QtWidgets.QDoubleSpinBox, self.aimFieldID[2]).value()]
        
        upVector=[self.findChild(QtWidgets.QDoubleSpinBox, self.upFieldID[0]).value(),
                  self.findChild(QtWidgets.QDoubleSpinBox, self.upFieldID[1]).value(),
                  self.findChild(QtWidgets.QDoubleSpinBox, self.upFieldID[2]).value()]
        
        wupVector=[self.findChild(QtWidgets.QDoubleSpinBox, self.wupFieldID[0]).value(),
                   self.findChild(QtWidgets.QDoubleSpinBox, self.wupFieldID[1]).value(),
                   self.findChild(QtWidgets.QDoubleSpinBox, self.wupFieldID[2]).value()]
        
        # check if locators were created or stored via selection
        if self.sortedLocIDs[0] == 'none' or self.sortedLocIDs[1] == 'none':
            # aim constraint setup via user selection
            locatorSelection=mc.ls(selection=True)
            if not locatorSelection:
                mc.warning('No locator selection made.')
                return
            if len(locatorSelection)!=2:
                mc.warning('Selection most only be 2 locators.')
                return
            # validate that exactly two locators have been selected
            startLocShp=mc.nodeType(mc.listRelatives(locatorSelection[0], s=True)[0])
            endLocShp=mc.nodeType(mc.listRelatives(locatorSelection[1], s=True)[0])
            if startLocShp not in self.available_locatorIDs or endLocShp not in self.available_locatorIDs: 
                mc.warning('Selection must only be two Locators for aim constraint setup.')
                return
            else:
                selStartLoc, selEndLoc = locatorSelection[0], locatorSelection[1]
                mc.aimConstraint(selEndLoc, selStartLoc, aim=aimVector, u=upVector, wu=wupVector)
                # create negative aim vector for end locator to aim at start locator
                negAimVector=[val*(-1) for val in aimVector]
                mc.aimConstraint(selStartLoc, selEndLoc, aim=negAimVector, u=upVector, wu=wupVector)
        else:
            # aim constraint setup via created/stored locators
            md.aim_constrain_locators(self.sortedLocIDs[0], self.sortedLocIDs[1], 
                           aimVector=aimVector, upVector=upVector, worldUpVector=wupVector)

    def orient_bnt_clicked(self):
        ''' Queries joint orientation checkbox values and calls orient_joints method. '''
        jointSelection=mc.ls(selection=True, type='joint')
        if not jointSelection:
            mc.warning('No Joint selection made.')
            return
        orientChildrenVal=self.orientChildCheck.isChecked()
        orientWorldVal=self.orientWorldCheck.isChecked()
        self.orient_joints(jointSelection, 
                           orientChildrenVal, orientWorldVal)

    def orient_joints(self, jointSelection, 
                      children:bool=True, jntToWorld:bool=False):
        ''' Orients selected joints with user provided settings. '''
        if jntToWorld:
            mc.joint(jointSelection, edit=True,
                     orientJoint='none', children=children)
        else:
            orientJoint=self.orientJntMenu.currentText()
            secAxis=self.secOrientMenu.currentText()
            mc.joint(jointSelection, edit=True, 
                     orientJoint=orientJoint, secondaryAxisOrient=secAxis, children=children)
        
    def joints_rotOrder(self):
        ''' Sets the rotation order for the selected joints based on user menu selection. '''
        jointSelection=mc.ls(selection=True, type='joint')
        if not jointSelection:
            mc.warning('No Joint selection made.')
            return
        rotOrder=self.rotOrderMenu.currentText()
        mc.joint(jointSelection, edit=True, rotationOrder=rotOrder, children=True)

    def mirror_joints(self):
        ''' Stores user settings and mirror the selected joints. '''
        mirrorAxisVal=self.mirrorAxisMenu.currentText()
        mirrorFuncVal=self.mirrorFuncMenu.currentText()
        searchFieldVal=self.searchField.text()
        replaceFieldVal=self.replaceField.text()
        includeLocators=self.transferCheck.isChecked()

        mirroredJnts=md.mirror_joints(mirrorAxis=mirrorAxisVal, mirrorFunc=mirrorFuncVal,
                                     search=searchFieldVal, replace=replaceFieldVal, 
                                     includeLocators=includeLocators)
        if not mirroredJnts:
            mc.warning('No Joint selection made.')
            return
        
        return mirroredJnts

    def build_joint_chain(self):
        ''' Handles the joint chain creation between the two created/selected locators. '''

        if self.startParentCheck.isChecked():
            # get starting joint name from user selection
            startJntName=mc.ls(selection=True, type='joint')
            # validate that only a single joint has been selected
            if not startJntName or len(startJntName) !=1 or mc.objectType(startJntName[0]) != 'joint':
                mc.warning('Please select only one Joint to be the starting Joint.')
                return
            startJntName=startJntName[0]
        else:
            startJntName=self.jntStartField.text()
            # validate that user has provided a start joint name before continuing
            if not startJntName:
                mc.warning('Please set a name for the Start Joint.')
                return
        # validate that user has provided an end joint name before continuing
        endJntName=self.jntEndField.text()
        if not endJntName:
            mc.warning('Please set a name for the End Joint.')
            return

        if self.jntMidFields:
            # get the text values of each created middle joint field and store it 
            midJntNames=[]
            # validate that middle fields contain text value
            for jntMidField in self.jntMidFields:
                midJntName=jntMidField.text()
                if not midJntName:
                    mc.warning('Please set a name for each of the Middle Joints')
                    return
                midJntNames.append(midJntName)
            # store middle names in between the start and end name items
            jntNames=[startJntName, *midJntNames, endJntName]
        else:
            jntNames=[startJntName, endJntName]

        if self.continueParentCheck.isChecked():
            # get parent joint from user selection
            parentJnt=mc.ls(selection=True, type='joint')
            # validate that only a single joint has been selected
            if not parentJnt or len(parentJnt) !=1 or mc.objectType(parentJnt[0]) != 'joint':
                mc.warning('Please select only one joint to parent.')
                return
            parentJnt=parentJnt[0]
        else:
            parentJnt=None

        # query the world space position of both locators
        startLocPos=mc.xform(self.sortedLocIDs[0], query=True, ws=True, t=True)
        endLocPos=mc.xform(self.sortedLocIDs[1], query=True, ws=True, t=True)
        # convert to MPoint values
        startLocPoint=om2.MPoint(startLocPos)
        endLocPoint=om2.MPoint(endLocPos)
        overrideTempColor=4

        jntPrefix=self.jntPrefixField.text()
        jntSuffix=self.jntSuffixField.text()
        if self.orientCheck.isChecked():
            orientJoint=self.orientJntMenu.currentText()
            secAxis=self.secOrientMenu.currentText()
            rotOrder=self.rotOrderMenu.currentText()
            # build joint chain with orientation and rotation order settings
            joints=md.joint_chain(startLocPoint, endLocPoint, jntNames=jntNames,
                                      jntNums=self.jntCountField.value(), parentJnt=parentJnt,
                                      jntsRad=self.jntSizeField.value(),
                                      orientJoint=orientJoint, secAxisOrient=secAxis,
                                      rotationOrder=rotOrder, 
                                      prefix=jntPrefix, suffix=jntSuffix,
                                      overrideColor=overrideTempColor)
        else:
            # build joint chain in the direction of the start and end locators
            joints=md.joint_chain(startLocPoint, endLocPoint, jntNames=jntNames,
                                      jntNums=self.jntCountField.value(), parentJnt=parentJnt,
                                      jntsRad=self.jntSizeField.value(),
                                      prefix=jntPrefix, suffix=jntSuffix,
                                      overrideColor=overrideTempColor)
        self.sortedJntIDs=joints
        print('Joint Chain Built')

        # set up parent constraint from locator to joint if checkbox has been checked
        if self.parentConstCheck.isChecked():
            mc.parentConstraint(self.sortedLocIDs[0], self.sortedJntIDs[0]) # type: ignore
            mc.parentConstraint(self.sortedLocIDs[1], self.sortedJntIDs[-1]) # type: ignore
        
        # swap the joint builder button for the commit button
        self.show_or_hide_joint_count(hideLayout=True, hideButton=True)
        self.show_or_hide_commitLayout()
        
        # disconnect restart undo/redo commands to avoid ghost stacking
        self.undoArrow = self._reset_arrow_connections()[0]
        self.undoArrow.setDisabled(True)

    def delete_jnt_constraints(self):
        for joint in self.sortedJntIDs:
            if mc.listConnections(joint, type='parentConstraint'):
                delConst=mc.listConnections(joint, type='parentConstraint')[0]
                mc.delete(delConst)
                print(f'{delConst} has been deleted')

    def delete_locators(self):
        for locator in self.sortedLocIDs:
            if mc.objExists(locator):
                mc.delete(locator)
            print(f'{locator} has been deleted')

    def commit_jnt_structure(self):
        ''' 
        Start and End Joint create a parent constraint to their respective Locator.
        Should only be called as the last step in Joint builder as it resets UI and data. 
        '''
        # validate joints exists
        if len(self.sortedJntIDs) < 2:
            raise KeyError('Cannot commit structure: joint ID data is insufficient, missing or has been deleted.')
        
        # if locators exist, create parent constraint from start and end locators to their respective joints
        if mc.objExists(self.sortedLocIDs[0]):
            md.parent_locator_to_joint(self.sortedJntIDs[0], self.sortedLocIDs[0]) # type: ignore
        if mc.objExists(self.sortedLocIDs[-1]):
            md.parent_locator_to_joint(self.sortedJntIDs[-1], self.sortedLocIDs[-1]) # type: ignore

        # zero out starting joint transformation values (translate, rotate, scale, normal)
        mc.makeIdentity(self.sortedJntIDs[0], apply=True,
                        translate=True, rotate=True, scale=True)
        
        # store orientation and rotation order settings based on menus, other wise they are left as default      
        orientJoint=self.orientJntMenu.currentText()
        secAxis=self.secOrientMenu.currentText()
        rotOrder=self.rotOrderMenu.currentText()
        print((orientJoint, secAxis, rotOrder))

        mc.joint(self.sortedJntIDs, edit=True, orientJoint=orientJoint,
                 secondaryAxisOrient=secAxis, rotationOrder=rotOrder, children=True)
        
        # make end joint orient to world and have same orientation as previous/parent joint
        mc.joint(self.sortedJntIDs[-1], edit=True, orientJoint='none', children=True)

        # delete locators if option is checked
        delLoc=self.findChild(QtWidgets.QCheckBox, 'deleteLocCheck').isChecked()
        if delLoc:
            self.delete_locators()

        mirrorCheck=self.findChild(QtWidgets.QCheckBox, 'mirrorJntsCheck')
        if mirrorCheck.isChecked():
            # mirror the joint chain with user settings
            mc.select(self.sortedJntIDs[0])
            mirroredJnts=self.mirror_joints()
            print(mirroredJnts)
            mirrorLoc1=md.create_locator(mirroredJnts[0], suffix='_loc')

            mirrorLoc2=md.create_locator(mirroredJnts[-1], suffix='_loc')

            md.parent_locator_to_joint(mirroredJnts[0], mirrorLoc1)
            md.parent_locator_to_joint(mirroredJnts[-1], mirrorLoc2)
            mc.select(clear=True)

        # reset UI to initial state and clear data
        self.close_dialog_window()

        self.delete_data()
        self.show_or_hide_commitLayout(hide=True)
        self.enable_locBtn(self.startLocBtn, 
                           self.startLocField, 
                           self.startLocCheck,
                           buttonText='Create Start Locator')
        self.enable_locBtn(self.endLocBtn, 
                           self.endLocField, 
                           self.endLocCheck,
                           buttonText='Create End Locator')
        
        self.jntBuilderBtn.setVisible(True)
        self.jntBuilderBtn.setDisabled(True)
        self.show_or_hide_fields()
        self.findChild(QtWidgets.QFormLayout, 'locSizeFieldForm').setRowVisible(0, True)
        self.singleLocBtn.setVisible(True)

    def show_dialog_window(self):
        ''' 
        Creates and shows dialog window to confirm or continue editing joint structure.
        Window is used as pre-check in case user doesn't want to commit yet.
        '''
        # close the dialog window in-case an previous instance already exists
        self.close_dialog_window()
        # build dialog window with a vertical layout 
        dialogWindow=QtWidgets.QDialog(self)
        dialogWindow.setObjectName('dialogWindow')
        dialogWindow.setWindowTitle(WINDOW_TITLE)

        dialogLayout=self.layouts.create_or_get_verticalLayout('dialogLayout', dialogWindow, spacing=3, contentMargins=(5,5,5,5))

        infoText='Commit to Joint Structure?\n' \
                'Important: Commit removes parent and aim constraint from Joints and Locators respectively.\n' \
                'Start and End Joint create a parent constraint to their respective Locator.'
        self.widgets.create_label('dialogInfoText', infoText, dialogLayout, align=QtCore.Qt.AlignHCenter)

        # create buttons to confirm or deny process, aligned to the right side of the window
        commitVLayout=self.layouts.create_or_get_verticalLayout('commitVLayout', parentWidget=dialogWindow,
                                                                parentLayout=dialogLayout)
        deleteLocForm=QtWidgets.QFormLayout(dialogWindow, formAlignment=QtCore.Qt.AlignHCenter|QtCore.Qt.AlignBottom)
        self.widgets.create_checkbox('deleteLocCheck', 'Delete Staged Locators', deleteLocForm)
        commitVLayout.addLayout(deleteLocForm)

        buttonLayout=self.layouts.create_or_get_gridLayout('buttonLayout', parentWidget=dialogWindow, 
                                                           parentLayout=commitVLayout)
        buttonLayout.setAlignment(QtCore.Qt.AlignRight)

        self.widgets.create_button('backBtn', 'Continue Editing', buttonLayout, clickedCmd=self.close_dialog_window)
        self.widgets.create_button('confirmBtn', 'Confirm', buttonLayout, gridSet=(0,1), 
                                   clickedCmd=self.commit_jnt_structure)

        dialogWindow.show()

    def close_dialog_window(self):
        ''' Deletes any existing dialog window instances. '''
        dialogWindows=self.findChildren(QtWidgets.QDialog, 'dialogWindow')
        if dialogWindows:
            for outdated in dialogWindows:
                outdated.close()

    def _apply_style(self):
        mainBG="#222325"
        cardBG="#222325"

        buttonBG="#B4753A"
        buttonPress="#995E26"

        boxBG="#6B6866"
        boxFrame="#8C8886"

        frameColor="#C07733"
        accent="#D7CEC5"
        
        disabledColor="#2C3035"
        disabledText="#5E636A"

        checkIcon=os.path.join(self.baseDirectory, 
                               'icons', 'menuIconSelect_24.png')
        checkIcon.replace('\\', '/')
        aim='aimConstraint.png'
        orient='orientJoint.png'

        self.setStyleSheet(f"""
        QWidget#{WINDOW_ID} {{
            background: {mainBG};
            border: 1px solid #3a3d44;
            border-radius: 5px;
        }}
        QFrame#cardFrame {{
            background: {cardBG};
            border: 2px solid #3a3d44;
            border-radius: 10px;
            border-top: 2px solid {frameColor};
            border-bottom: 2px solid {frameColor};
        }}

        QFrame#aimFrame {{
            background: {cardBG};
            border: 2px dashed #3a3d44;
            border-radius: 10px;
            border-top: 2px solid {frameColor};
            border-bottom: 2px solid {frameColor};
        }}
        QFrame#orientFrame {{
            background: {cardBG};
            border: 2px dashed #3a3d44;
            border-radius: 10px;
            border-top: 2px solid {frameColor};
            border-bottom: 2px solid {frameColor};
        }}
        QFrame#mirrorFrame {{
            background: {cardBG};
            border: 2px dashed #3a3d44;
            border-radius: 10px;
            border-top: 2px solid {frameColor};
            border-bottom: 2px solid {frameColor};
        }}

        QLabel {{
            font-size: 13px;
            color: #ffffff;
        }}

        QCheckBox {{
            spacing: 4.5px;
            font-size: 13px;
            color: #FFFFFF;
        }}
        QCheckBox:hover {{
            color: {accent};
        }}
        QCheckBox::indicator {{
            width: 11px;
            height: 11px;
            background-color: {boxBG};
            border-radius: 2px;
            border: 1px solid {frameColor};
        }}
        QCheckBox::indicator:hover {{
            border: 1px solid {accent};
        }}
        QCheckBox::indicator:checked {{
            image: url(:/UVEditorIsolate.png);
        }}

        QRadioButton {{
            spacing: 4.5px;
            font-size: 12px;
            color: #FFFFFF;
        }}
        QRadioButton:hover {{
            color: {accent};
        }}
        QRadioButton::indicator {{
            width: 10px;
            height: 10px;
            background-color: {boxBG};
            border-radius: 5px;
            border: 1px solid {frameColor};
        }}
        QRadioButton::indicator:hover {{
            border: 1px solid {accent};
        }}
        QRadioButton::indicator:checked {{
            width: 10px;
            height: 10px;
            background-color: {accent};
            border-radius: 5px;
            border-color: gray;
        }}

        QLineEdit {{
            font-size: 13px;
            border: 2px solid {boxFrame};
            background: {boxBG};
            border-radius: 12px;
            padding: 6px 10px;
            color: #ffffff;
            selection-background-color: {accent};
        }}
        QLineEdit:focus {{
            border: 2px solid {accent};
        }}
        QLineEdit:disabled {{
            background: {disabledColor};
            border: 2px solid {disabledColor};
            color: {disabledText};
        }}

        QPushButton {{
            font-size: 13px;
            border: 2px solid {frameColor};
            background: {buttonBG};
            border-radius: 8px;
            padding: 7px 12px;
            color: #ffffff;
        }}
        QPushButton:hover {{
            border: 2px solid {accent};
        }}
        QPushButton:pressed {{
            background: {buttonPress};
        }}
        QPushButton:disabled {{
            background: {disabledColor};
            border: 2px solid {disabledColor};
            color: {disabledText};
        }}

        QComboBox {{
            font-size: 13px;
            border: 2px solid {boxFrame};
            background: {boxBG};
            border-radius: 5px;
            color: #ffffff;
        }}
        QComboBox:hover {{
            border: 2px solid {accent};
        }}
        QComboBox:focus {{
            border: 2px solid {accent};
        }}
        QComboBox:disabled {{
            background: {disabledColor};
            border: 2px solid {disabledColor};
            color: {disabledText};
        }}
        QComboBox::down-arrow {{
            width: 8px;
            height: 8px;
            color: #ffffff;
        }}

        QComboBox QAbstractItemView {{
            background: {mainBG};
            color: #ffffff;
            selection-background-color: {buttonBG};
            border: 1px solid #3a3d44;
        }}

        QSpinBox {{
            font-size: 11px;
            border: 1px solid {frameColor};
            background: {boxBG};
            border-radius: 5px;
            color: #ffffff;
            selection-background-color: {buttonBG};
        }}
        QSpinBox:focus {{
            border: 1px solid {accent};
        }}
        QSpinBox:disabled {{
            background: {disabledColor};
            border: 1px solid {disabledColor};
            color: {disabledText};
        }}

        QDoubleSpinBox {{
            font-size: 11px;
            border: 1px solid {frameColor};
            background: {boxBG};
            border-radius: 5px;
            color: #ffffff;
            selection-background-color: {buttonBG};
        }}
        QDoubleSpinBox:focus {{
            border: 1px solid {accent};
        }}
        QDoubleSpinBox:disabled {{
            background: {disabledColor};
            border: 1px solid {disabledColor};
            color: {disabledText};
        }}

        QSlider::groove:horizontal{{
            height: 4px;
            background: #ffffff;
            border-radius: 2px;
        }}
        QSlider::handle:horizontal{{
            width: 16px;
            height: 16px;
            margin: -6px 0;
            background: {buttonBG};
            border: 2px solid {frameColor};
            border-radius: 6px;
        }}
        QSlider::handle:horizontal:hover {{
            border: 2px solid {accent};
        }}
        """)

    def _reset_arrow_connections(self):
        ''' Private method to disconnect undo/redo arrow button signals for repeated use. '''

        for arrowBtn in (self.undoArrow, self.redoArrow):
            try:
                arrowBtn.clicked.disconnect()
            except (RuntimeError, TypeError):
                pass # nothing has been connected

        return self.undoArrow, self.redoArrow
    
