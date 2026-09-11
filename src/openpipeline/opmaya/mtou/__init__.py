import importlib

import maya.cmds as mc

from . import dock_wrapper


def load(*args):
    importlib.reload(dock_wrapper)  
    if mc.menu('UExporterMenu', exists = True):
        mc.deleteUI('UExporterMenu', menu = True)

    main_menu = mc.menu('UExporterMenu', label = 'Exporter Tools', parent = 'MayaWindow', tearOff = True)

    mc.menuItem(label='MayaToUnreal', command = dock_wrapper.mtouUI, parent = main_menu)

def unload(*args):
    dock_wrapper.mtouUI(run=False)

    if mc.menu('UExporterMenu', exists = True):
        mc.deleteUI('UExporterMenu', menu = True)
