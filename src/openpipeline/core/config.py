import os
from pathlib import Path

from . import data_utils as dutil


def load_config(project_name: str, set_root=False) -> dict:
    ''' Returns configuration data from JSON file for the specified project. '''

    # find current working directory
    opi_path = os.path.dirname(os.getcwd())
    opi_path = Path(os.path.dirname(__file__)).parents[1]

    proj_path = Path(opi_path, 'projects', project_name)

    proj_data = dutil.load_data(proj_path, 'project.json')

    if set_root:
        proj_data["project_root"] = str(proj_path).replace('\\', '/')
        dutil.save_data(proj_path, 'project.json', proj_data)

    return proj_data 

