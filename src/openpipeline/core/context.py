import os
from pathlib import Path


class ProjContext:
    def __init__(self, proj_data:dict):
        ''' 
        Args: system: str - the system type [unix or windows] to use for the project root path.
        '''
        # collect project data as attributes
        self.__proj_data = proj_data
        self.__root = self.get_project_root()
        self.name = self.__proj_data['project_name']
        self.version = self.__proj_data['pipeline_version']

        self.assets = self.__root / self.__proj_data['directories']['assets']
        self.export = self.__root / self.__proj_data['directories']['export']

        self.opmaya_reg = self.__proj_data['tools']['opmaya']

    def get_project_root(self) -> Path:
        proj_path = self.__proj_data['project_root']
        parent_path = Path(os.path.dirname(__file__)).parents[2]
        root_path = parent_path / proj_path

        return root_path # provides Home directory within path for unix systems
