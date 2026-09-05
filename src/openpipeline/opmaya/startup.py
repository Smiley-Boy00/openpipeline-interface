## script should be called from the opi_maya plugin script
import maya.cmds as mc
from . import mtou

def initializer():
    print('Initializing OPI plugin.')
    
    if mc.menu('UExporterMenu', exists = True):
        mc.deleteUI('UExporterMenu', menu = True)

    main_menu = mc.menu('UExporterMenu', label = 'Exporter Tools', parent = 'MayaWindow', tearOff = True)

    mc.menuItem(label='MayaToUnreal', command = mtou.load, parent = main_menu)

def uninitializer():
    print('Deactivating OPI plugin.')

    if mc.menu('UExporterMenu', exists = True):
        mc.deleteUI('UExporterMenu', menu = True)