import json
import os


# data handling related functions
def load_config(project_name: str) -> dict:
    ''' Returns configuration data from JSON file for the specified project. '''

    # find current working directory
    # check if path already includes pysrc 
    if 'pysrc' in os.path.dirname(os.getcwd()):
        proj_path = os.path.join(os.path.dirname(os.getcwd()), 'projects', project_name)
    else:
        proj_path = os.path.join(os.path.dirname(os.getcwd()), 'pysrc', 'projects', project_name)
    config_file = os.path.join(proj_path, 'project.json')

    with open(config_file) as file:
        proj_data = json.load(file) 
        return proj_data 
    