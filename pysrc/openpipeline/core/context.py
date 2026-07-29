import sys


class ProjContext():
    def __init__(self, config_data:dict, system:str):
        ''' 
        Args: system: str - the system type (Unix or Windows) to use for the project root path.
        '''
        self.name = config_data['project_name']
        self.version = config_data['pipeline_version']
        self.project_root = config_data['project_root'][system]
        self.directories = config_data['directories']