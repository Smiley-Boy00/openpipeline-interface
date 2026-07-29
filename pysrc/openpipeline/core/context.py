import sys


class ProjContext():
    def __init__(self, config_data:dict):
        self.name = config_data.get('project_name')
        self.version = config_data.get('pipeline_version')
        self.directories = config_data.get('directories')