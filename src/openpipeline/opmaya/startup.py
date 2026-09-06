## script should be called from the opi_maya plugin script
import maya.cmds as mc
from . import mtou

def initializer():
    print('Initializing OPI plugin.')
    
    mtou.load()

def uninitializer():
    print('Deactivating OPI plugin.')

    mtou.unload()