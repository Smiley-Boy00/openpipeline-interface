from pathlib import Path

import subprocess
import os

def build_maya_mod(mod_path:Path):
    op_path = os.path.dirname((os.getcwd()))

    mod_path = str(mod_path.expanduser())
    if not os.path.exists(mod_path):
        os.makedirs(mod_path, exist_ok=True)
    
    mod_file = os.path.join(mod_path, 'OPMaya.mod')

    if not os.path.exists(mod_file):
        f = open(mod_file, 'x')

    with open(mod_file, 'w') as f:
        f.write(f"""+ OpenPipeline 0.1.0 {op_path}
PYTHONPATH +:= pysrc""")

def find_module_paths(os:str, version:str='2026'):
    '''Args: 
    os ['darwin', 'linux', 'windows']
    version ['2026', '2027', ...]
    '''
    os_flags = ['darwin', 'linux', 'windows']
    if os not in os_flags:
        raise ValueError(f"Incorrect os flag: [{os}]. Use {os_flags}")
    
    mayapy_path = {'darwin':f'/Applications/Autodesk/maya{version}/Maya.app/Contents/bin/mayapy',
                   'windows': fr'C:\Program Files\Autodesk\Maya{version}\bin\mayapy.exe',
                   'linux': f'/usr/autodesk/maya{version}/bin/mayapy'}

    if os == 'darwin' or os == 'linux':
        to_split = ':'
    else:
        to_split = ';'

    maya_script = f'''
import os
import maya.standalone

maya.standalone.initialize(name="python")

for path in os.environ.get("MAYA_MODULE_PATH").split("{to_split}"):
    print(path)

maya.standalone.uninitialize()
    '''
    result = subprocess.run([mayapy_path[os], '-c', maya_script],
                            capture_output=True,
                            text=True)
    if result.returncode != 0:
        print(result.stderr)
        return

    print(result.stdout.strip())