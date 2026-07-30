import json
import os


# data handling related functions
def load_config() -> dict:
    ''' Loads a path data (dictionary) from a json file. '''

    # find current working directory
    if 'pysrc' in os.path.dirname(os.getcwd()):
        proj_path = os.path.join(os.path.dirname(os.getcwd()), 'data')
    else:
        proj_path = os.path.join(os.path.dirname(os.getcwd()), 'pysrc', 'data')
    config_file = os.path.join(proj_path, 'project.json')

    with open(config_file) as file:
        proj_data = json.load(file) 
        return proj_data
    