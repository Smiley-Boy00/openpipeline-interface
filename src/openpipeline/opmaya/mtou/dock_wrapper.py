import importlib

import maya.cmds as mc
from PySide6 import QtWidgets

from ..wrapperQt import qt_utils
from . import main_ui

__WORKSPACE_NAME='mtouWorkspace'
__WINDOW_ID='mtouExporter'

def build_wrapper():
    qt_control=qt_utils.get_control_pointer(__WORKSPACE_NAME)
    qt_layout:QtWidgets.QLayout=qt_control.layout() # pyright: ignore[reportAssignmentType]

    importlib.reload(main_ui)
    main_ui.mtouExporterUI(__WINDOW_ID)

    ui_instance = qt_utils.get_control_pointer(__WINDOW_ID)
    qt_layout.addWidget(ui_instance)

    
def mtouUI(*args, run=True):
    if run:
        if mc.workspaceControl(__WORKSPACE_NAME, exists=True):
            mc.workspaceControl(__WORKSPACE_NAME, edit=True, restore=True)

        else:
            workspace_control=mc.workspaceControl(__WORKSPACE_NAME, label='Maya To Unreal Exporter',
                                                dockToMainWindow=('right', False), retain=False,
                                                uiScript=f"import {__name__}; {__name__}.build_wrapper()")

    else:
        if mc.workspaceControl(__WORKSPACE_NAME, exists=True):
            mc.workspaceControl(__WORKSPACE_NAME, edit=True, close=True)
