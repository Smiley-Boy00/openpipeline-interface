import importlib

import maya.cmds as mc

from . import main_ui

## insert code to make mtou ui dockable inside maya

def load(*args):
    if mc.menu('UExporterMenu', exists = True):
        mc.deleteUI('UExporterMenu', menu = True)

    main_menu = mc.menu('UExporterMenu', label = 'Exporter Tools', parent = 'MayaWindow', tearOff = True)

    mc.menuItem(label='MayaToUnreal', command = run_mtouUI, parent = main_menu)

def unload(*args):
    if mc.menu('UExporterMenu', exists = True):
        mc.deleteUI('UExporterMenu', menu = True)

def run_mtouUI(*args):
    importlib.reload(main_ui)
    main_ui.mtouExporterUI()