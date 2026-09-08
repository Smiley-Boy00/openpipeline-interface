import os
import subprocess
from pathlib import Path


def build_maya_mod(mod_path:Path):
    '''Creates a .mod file containing the package path information. 
    
    Args
    ----------
    mod_path : Path
        Directory path where the .mod file will be generated.
    '''
    op_path = os.getcwd()

    mod_path = str(mod_path.expanduser())
    if not os.path.exists(mod_path):
        os.makedirs(mod_path, exist_ok=True)
    
    mod_file = os.path.join(mod_path, 'OPMaya.mod')

    if not os.path.exists(mod_file):
        f = open(mod_file, 'x')

    with open(mod_file, 'w') as f:
        f.write(f"""+ OpenPipeline 0.1.0 {os.getcwd()}
PYTHONPATH +:= src""")

def build_op_plugin(plugin_path:Path) :
    plugin_path = str(plugin_path.expanduser())

    if not os.path.exists(plugin_path):
        os.makedirs(plugin_path, exist_ok=True)

    plugin_file = os.path.join(plugin_path, 'OPMaya.py')

    script = '''
import maya.api.OpenMaya as om
from openpipeline.opmaya import startup

# connect to the OpenMaya API 2.0
maya_useNewAPI = True

def initializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin, 'OPI', '0.1.0')
    startup.initializer()

def uninitializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    startup.uninitializer()
    '''

    with open(plugin_file, 'w') as f:
        f.write(script)

def find_paths(os:str, environ:str, version:str='2026'):
    '''Prints the available maya module directories based on operation system. 

    Args
    ----------
    os : str
        Must only be the currently running system: 'darwin', 'linux' or 'windows' 
    version : str
        Finds the directories for the installed maya version.
    '''
    os_flags = ['darwin', 'linux', 'windows']
    if os not in os_flags:
        raise ValueError(f"Incorrect os flag: [{os}]. Use {os_flags}")

    # store fixed mayapy executable for each os
    mayapy_path = {'darwin':f'/Applications/Autodesk/maya{version}/Maya.app/Contents/bin/mayapy',
                   'windows': fr'C:\Program Files\Autodesk\Maya{version}\bin\mayapy.exe',
                   'linux': f'/usr/autodesk/maya{version}/bin/mayapy'}

    if os == 'darwin' or os == 'linux':
        to_split = ':'
    else:
        to_split = ';'

    # get maya modules with headless maya environment  
    maya_script = f'''
import os
import maya.standalone

maya.standalone.initialize(name="python")

for path in os.environ.get("{environ}").split("{to_split}"):
    print(path)

maya.standalone.uninitialize()
    '''
    result = subprocess.run([mayapy_path[os], '-c', maya_script],
                            capture_output=True,
                            text=True)
    if result.returncode != 0:
        print(result.stderr)
        return

    print(result.stdout.strip()) # .strip() provides output without blank newlines