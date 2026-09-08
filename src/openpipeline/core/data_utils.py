import json
import os
import platform
from pathlib import Path


# data handling related functions
def save_data(path:str | Path, file_name:str, data) -> None:
    ''' Saves data into a json file: must include a path to store data. '''
    if not file_name.endswith('.json'):
        file_name+='.json'

    if type(path) == Path:
        full_path = path / file_name
    else:
        full_path = os.path.join(path, file_name)

    with open(full_path, 'w') as file:
        json.dump(data, file, indent=4, sort_keys=True)

def load_data(path:str | Path, file_name:str) -> dict:
    ''' Loads a path data (dictionary) from a json file. '''

    if type(path) == Path:
        full_path = path / file_name
    else:
        full_path = os.path.join(path, file_name)
    
    with open(full_path, 'r') as file:
        stored_data = json.load(file)

    return stored_data

# directory related functions

def get_os() -> str:
    system = platform.system().lower()
    if system in ('darwin', 'linux'):
        system = 'unix'
    return system

def get_documents_folder() -> str:
    ''' Finds the documents path inside the user's home directory. '''
    documents_path = os.path.join(str(Path.home()), 'Documents')
    return documents_path

def path_exists(file_path: str) -> bool:
    ''' Checks if a path or file path exists. '''
    return os.path.exists(file_path)
    

