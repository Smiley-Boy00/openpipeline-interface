import maya.OpenMayaUI as omui
from PySide6 import QtWidgets
from shiboken6 import wrapInstance


def get_main_maya_window() -> QtWidgets.QWidget:
    maya_ptr = omui.MQtUtil.mainWindow()
    maya_window: QtWidgets.QWidget = wrapInstance(int(maya_ptr), QtWidgets.QWidget)
    return maya_window

def get_control_pointer(pointer_name) -> QtWidgets.QWidget:
    pointer = omui.MQtUtil.findControl(pointer_name)
    control: QtWidgets.QWidget = wrapInstance(int(pointer), QtWidgets.QWidget)
    return control