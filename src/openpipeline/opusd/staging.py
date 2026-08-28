import subprocess
from pxr import Usd

def create_new_stage(file_path:str):
    ''' 
    File path must include usd file extension.
    Returns a USD stage created from the provided file path.
    '''
    stage: Usd.Stage = Usd.Stage.CreateNew(file_path)
    return stage

def run_usdview_stage(file_path:str):
    subprocess.run(['usdview', file_path], stderr=subprocess.PIPE)