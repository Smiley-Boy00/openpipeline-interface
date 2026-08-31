from PySide6 import QtCore, QtWidgets

class wrapWid():
    ''' A wrapper class for commonly used Qt Widgets, gets the widget if it already exists. '''
    def __init__(self, parentUI:QtWidgets.QWidget):
        ''' Initializes the QWidget methods, parented to the called UI. '''
        self.parentUI=parentUI

    def create_button(self, widgetID:str, label:str,
                      parentLayout:QtWidgets.QFormLayout|QtWidgets.QBoxLayout|QtWidgets.QGridLayout,
                      enabled:bool=True, visible:bool=True,
                      margins:tuple[int,int,int,int]=(0,0,0,0),
                      gridSet:tuple[int,int]=(0,0), clickedCmd=None):
        ''' Returns a built or obtained QPushButton widget based on the widgetID. '''

        buttonWidget=QtWidgets.QPushButton(label, parent=self.parentUI)
        buttonWidget.setObjectName(widgetID)
        if clickedCmd:
            buttonWidget.clicked.connect(clickedCmd)

        buttonWidget.setContentsMargins(*margins)
        if not visible:
            buttonWidget.hide()
        buttonWidget.setEnabled(enabled)
        if isinstance(parentLayout, QtWidgets.QGridLayout):
            parentLayout.addWidget(buttonWidget, gridSet[0], gridSet[1])
        else:
            parentLayout.addWidget(buttonWidget)
        return buttonWidget

    def create_arrowButton(self, widgetID:str, 
                           parentLayout:QtWidgets.QFormLayout|QtWidgets.QBoxLayout|QtWidgets.QGridLayout,
                           direction:str='left', enabled:bool=True, visible:bool=True, 
                           iconSize:QtCore.QSize=QtCore.QSize(15,15),
                           styleSheet:str='', gridSet:tuple[int,int]=(0,0)):
        ''' Returns a built or obtained QToolButton as an arrow widget based on the widgetID. '''

        arrow_types={'left':QtCore.Qt.LeftArrow, 'right':QtCore.Qt.RightArrow,
                     'up':QtCore.Qt.UpArrow, 'down':QtCore.Qt.DownArrow}
        if not arrow_types.get(direction):
            raise ValueError(f'{direction} is not a valid arrow direction, use: ["left", "right", "up", "down"]')
        
        arrowButtonWidget=QtWidgets.QToolButton(parent=self.parentUI)
        arrowButtonWidget.setObjectName(widgetID)
        arrowButtonWidget.setArrowType(arrow_types.get(direction))
        arrowButtonWidget.setIconSize(iconSize)
        if styleSheet:
            arrowButtonWidget.setStyleSheet(styleSheet)

        if not visible:
            arrowButtonWidget.hide()
        arrowButtonWidget.setEnabled(enabled)
        if isinstance(parentLayout, QtWidgets.QGridLayout):
            parentLayout.addWidget(arrowButtonWidget, gridSet[0], gridSet[1])
        else:
            parentLayout.addWidget(arrowButtonWidget)
        return arrowButtonWidget

    def create_numField(self, widgetID:str, parentLayout:QtWidgets.QBoxLayout|QtWidgets.QGridLayout,
                        type='int', label:str='', numVal:int|float=0, minVal:int|float=0, maxVal:int|float=10,
                        enabled:bool=True, visible:bool=True, width=50,
                        margins:tuple[int,int,int,int]=(0,0,0,0), 
                        gridSet:tuple[int,int]=(0,0), align=None):
        ''' Returns a built or obtained QSpinBox or QDoubleSpinBox widget based on the widgetID. '''

        available_type=['int', 'float']
        if type not in available_type:
            raise ValueError(f'{type} is not a valid Num Field type, use: {available_type}')
        if type=='int':
            numField=QtWidgets.QSpinBox
        else:
            numField=QtWidgets.QDoubleSpinBox

        fieldWidget=numField(parent=self.parentUI)
        fieldWidget.setObjectName(widgetID)

        fieldWidget.setMinimum(minVal)
        fieldWidget.setMaximum(maxVal)
        fieldWidget.setValue(numVal)
        fieldWidget.setMinimumWidth(width)
        fieldWidget.setContentsMargins(*margins)
        fieldWidget.setEnabled(enabled)
        if label:
            formLayout=QtWidgets.QFormLayout()
            formLayout.setObjectName(f'{widgetID}Form')
            formLayout.addRow(label, fieldWidget)
            if not visible:
               formLayout.setRowVisible(0, False)
            if align:
                formLayout.setFormAlignment(align)
            if isinstance(parentLayout, QtWidgets.QGridLayout):
                parentLayout.addLayout(formLayout, gridSet[0], gridSet[1])
            else:
                parentLayout.addLayout(formLayout)
        else:
            fieldWidget.hide()

            if isinstance(parentLayout, QtWidgets.QGridLayout):
                parentLayout.addWidget(fieldWidget, gridSet[0], gridSet[1])
            else:
                parentLayout.addWidget(fieldWidget)
        return fieldWidget

    def create_textField(self, widgetID:str, 
                         parentLayout:QtWidgets.QBoxLayout|QtWidgets.QGridLayout, 
                         label:str|None=None, text:str='', placeholderText:str='', 
                         enabled:bool=True, visible:bool=True, 
                         margins:tuple[int,int,int,int]=(0,0,0,0), 
                         gridSet:tuple[int,int]=(0,0), align=None):
        ''' Returns a built or obtained QLineEdit widget based on the widgetID. '''
        
        fieldWidget=QtWidgets.QLineEdit()
        fieldWidget.setObjectName(widgetID)

        fieldWidget.setText(text)
        fieldWidget.setPlaceholderText(placeholderText)
        fieldWidget.setContentsMargins(*margins)
        if align:
            fieldWidget.setAlignment(align)
        fieldWidget.setEnabled(enabled)
        if label:
            formLayout=QtWidgets.QFormLayout()
            formLayout.setObjectName(f'{widgetID}Form')
            formLayout.addRow(label, fieldWidget)
            if not visible:
                formLayout.setRowVisible(0, False)
        
            if isinstance(parentLayout, QtWidgets.QGridLayout):
                parentLayout.addLayout(formLayout, gridSet[0], gridSet[1])
            else:
                parentLayout.addLayout(formLayout)
        else:
            if not visible:
                fieldWidget.hide()

            if isinstance(parentLayout, QtWidgets.QGridLayout):
                parentLayout.addWidget(fieldWidget, gridSet[0], gridSet[1])
            else:
                parentLayout.addWidget(fieldWidget)
        return fieldWidget

    def create_checkbox(self, widgetID:str, label:str,
                        parentLayout:QtWidgets.QFormLayout|QtWidgets.QBoxLayout|QtWidgets.QGridLayout,
                        enabled:bool=True, visible:bool=True, value:bool=False, 
                        gridSet:tuple[int,int]=(0,0), align=None,
                        clickedCmd=None):
        ''' Returns a built or obtained QCheckBox widget based on the widgetID. '''
        
        checkboxWidget=QtWidgets.QCheckBox(label, parent=self.parentUI)
        checkboxWidget.setObjectName(widgetID)
        if clickedCmd:
            checkboxWidget.clicked.connect(clickedCmd)

        if not visible:
            checkboxWidget.hide()
        checkboxWidget.setChecked(value)
        checkboxWidget.setEnabled(enabled)
        if isinstance(parentLayout, QtWidgets.QGridLayout):
            if align:
                parentLayout.addWidget(checkboxWidget, gridSet[0], gridSet[1], align)
            else:
                parentLayout.addWidget(checkboxWidget, gridSet[0], gridSet[1])
        else:
            parentLayout.addWidget(checkboxWidget)
        return checkboxWidget

    def create_radialButton(self, widgetID:str, label:str,
                            parentLayout:QtWidgets.QFormLayout|QtWidgets.QBoxLayout|QtWidgets.QGridLayout,
                            enabled:bool=True, visible:bool=True, value:bool=False, 
                            gridSet:tuple[int,int]=(0,0), align=None,
                            clickedCmd=None):
        ''' Returns a built or obtained QCheckBox widget based on the widgetID. '''
        
        radioButtonWidget=QtWidgets.QRadioButton(label, parent=self.parentUI)
        radioButtonWidget.setObjectName(widgetID)
        if clickedCmd:
            radioButtonWidget.clicked.connect(clickedCmd)

        if not visible:
            radioButtonWidget.hide()
        radioButtonWidget.setChecked(value)
        radioButtonWidget.setEnabled(enabled)
        if isinstance(parentLayout, QtWidgets.QGridLayout):
            if align:
                parentLayout.addWidget(radioButtonWidget, gridSet[0], gridSet[1], align)
            else:
                parentLayout.addWidget(radioButtonWidget, gridSet[0], gridSet[1])
        else:
            parentLayout.addWidget(radioButtonWidget)
        return radioButtonWidget

    def create_slider(self, widgetID:str, 
                      parentLayout:QtWidgets.QFormLayout|QtWidgets.QBoxLayout|QtWidgets.QGridLayout,
                      orientation:QtCore.Qt.Horizontal|QtCore.Qt.Vertical,
                      interval:int=1, value:int=0, minVal:int=0, maxVal:int=10,
                      enabled:bool=True, visible:bool=True, width=50,
                      gridSet:tuple[int,int]=(0,0), align=None):
        ''' Returns a built or obtained QSlider widget based on the widgetID. '''
        
        sliderWidget=QtWidgets.QSlider(orientation, parent=self.parentUI)
        sliderWidget.setObjectName(widgetID)

        sliderWidget.setMinimum(minVal)
        sliderWidget.setMaximum(maxVal)
        sliderWidget.setTickInterval(interval)
        sliderWidget.setValue(value)
        sliderWidget.setMinimumWidth(width)
        if not visible:
            sliderWidget.hide()
        sliderWidget.setEnabled(enabled)
        if isinstance(parentLayout, QtWidgets.QGridLayout):
            if align:
                parentLayout.addWidget(sliderWidget, gridSet[0], gridSet[1], align)
            else:
                parentLayout.addWidget(sliderWidget, gridSet[0], gridSet[1])
        else:
            parentLayout.addWidget(sliderWidget)
        return sliderWidget

    def create_label(self, widgetID:str, label:str,
                     parentLayout:QtWidgets.QBoxLayout|QtWidgets.QGridLayout,
                     enabled:bool=True, visible:bool=True,
                     gridSet:tuple[int,int]=(0,0), align=None):
        ''' Returns a built or obtained QLabel widget based on the widgetID. '''

        labelWidget=QtWidgets.QLabel(label, parent=self.parentUI)
        labelWidget.setObjectName(widgetID)
        if align:
            labelWidget.setAlignment(align)
        if not visible:
            labelWidget.hide()
        labelWidget.setEnabled(enabled)
        if isinstance(parentLayout, QtWidgets.QGridLayout):
            parentLayout.addWidget(labelWidget, gridSet[0], gridSet[1])
        else:
            parentLayout.addWidget(labelWidget)
        return labelWidget
