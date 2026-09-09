import os
from pathlib import Path

from . import data_utils as dutil


def load_config(project_name: str) -> dict:
    ''' Returns configuration data from JSON file for the specified project. '''

    # find current working directory
    opi_path = Path(os.path.dirname(__file__)).parents[1]
    proj_path = Path(opi_path, 'projects', project_name)

    proj_data = dutil.load_data(proj_path, 'project.json')

    return proj_data 

