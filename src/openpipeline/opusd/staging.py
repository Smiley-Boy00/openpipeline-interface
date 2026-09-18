import subprocess

from pxr import Usd


def create_or_open_stage(stage_path:str, create:bool=False):
    ''' 
    File path must include usd file extension.
    Returns a USD stage from the provided file path.
    '''
    if create:
        stage: Usd.Stage = Usd.Stage.CreateNew(stage_path)
    else:
        stage: Usd.Stage = Usd.Stage.Open(stage_path)
    return stage

def run_usdview_stage(stage_path:str):
    subprocess.Popen(['usdview', stage_path], stderr=subprocess.PIPE)

def get_property_names(prim: Usd.Prim, attrOnly=False):
    if attrOnly:
        for attr in prim.GetAttributes():
                str_split = str(attr).split(".")[-1].split("GetAttribute")[-1]
                attr_name = str_split.strip("(')")
                print(attr_name)
    else:
        for prop_name in prim.GetPropertyNames():
            print(prop_name)
