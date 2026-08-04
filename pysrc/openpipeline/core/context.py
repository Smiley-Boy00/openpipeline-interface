import platform
import sys

from pathlib import Path

class ProjContext():
    def __init__(self, proj_data:dict):
        ''' 
        Args: system: str - the system type [unix or windows] to use for the project root path.
        '''
        # collect project data as attributes
        self._proj_data = proj_data
        self.name = self._proj_data['project_name']
        self.version = self._proj_data['pipeline_version']
        self.root = self.get_project_root()

        self.assets = self.root / self._proj_data['directories']['assets']
        self.export = self.root / self._proj_data['directories']['export']

    def get_project_root(self) -> Path:
        system = platform.system().lower() # find OS, keep it lowercase

        if system in ('darwin', 'linux'):
            system = 'unix'

        root_path = self._proj_data['project_root'][system]

        return Path(root_path).expanduser() # provides Home directory within path for unix systems