from PySide6 import QtCore, QtWidgets

class wrapLay():
    ''' A wrapper class for commonly used Qt Layouts, gets the layout if it already exists. '''
    def __init__(self, parentUI:QtWidgets.QWidget):
        ''' Initializes the QWidget methods, parented to the called UI. '''
        self.parentUI=parentUI
        
    def create_or_get_verticalLayout(self, layoutID:str,  
                                     parentWidget:QtWidgets.QWidget|None=None,
                                     parentLayout:QtWidgets.QBoxLayout|QtWidgets.QGridLayout|None=None,
                                     spacing=5, contentMargins:tuple[int,int,int,int]=(0,0,0,0)):
        ''' Returns a built or obtained QVBoxLayout based on the layoutID. '''
        if not parentWidget:
            parentWidget=self.parentUI

        boxLayout=parentWidget.findChild(QtWidgets.QVBoxLayout, layoutID)
        if not boxLayout:
            boxLayout=QtWidgets.QVBoxLayout(parentWidget)
            boxLayout.setObjectName(layoutID)
            if parentLayout:
                parentLayout.addLayout(boxLayout)
        boxLayout.setSpacing(spacing)
        boxLayout.setContentsMargins(*contentMargins)
        
        return boxLayout

    def create_or_get_horizontalLayout(self, layoutID:str,
                                       parentWidget:QtWidgets.QWidget|None=None,
                                       parentLayout:QtWidgets.QBoxLayout|QtWidgets.QGridLayout|None=None,
                                       spacing=5, contentMargins:tuple[int,int,int,int]=(0,0,0,0)):
        ''' Returns a built or obtained QHBoxLayout based on the layoutID. '''
        if not parentWidget:
            parentWidget=self.parentUI

        boxLayout=parentWidget.findChild(QtWidgets.QHBoxLayout, layoutID)
        if not boxLayout:
            boxLayout=QtWidgets.QHBoxLayout(parentWidget)
            boxLayout.setObjectName(layoutID)
            if parentLayout:
                parentLayout.addLayout(boxLayout)
        boxLayout.setSpacing(spacing)
        boxLayout.setContentsMargins(*contentMargins)
        
        return boxLayout

    def create_or_get_gridLayout(self, layoutID:str, 
                                 parentWidget:QtWidgets.QWidget|None=None,
                                 parentLayout:QtWidgets.QBoxLayout|QtWidgets.QGridLayout|None=None,
                                 contentMargins:tuple[float,float,float,float]=(0,0,0,0)):
        ''' Returns a built or obtained QGridLayout based on the layoutID. '''
        if not parentWidget:
            parentWidget=self.parentUI

        gridLayout=parentWidget.findChild(QtWidgets.QGridLayout, layoutID)
        if not gridLayout:
            gridLayout=QtWidgets.QGridLayout(parentWidget)
            gridLayout.setObjectName(layoutID)
            if parentLayout:
                parentLayout.addLayout(gridLayout)
        
        gridLayout.setContentsMargins(*contentMargins)

        return gridLayout
    

    
