from pathlib import Path
import json
import os

# data handling related functions
def save_data(path:str, file_name:str, data) -> None:
    ''' Saves data into a json file: must include a path to store data. '''
    if not file_name.endswith('.json'):
        file_name+='.json'

    with open(os.path.join(path, file_name), 'w') as file:
        json.dump(data, file, indent=4, sort_keys=True)

def load_data(path:str, file_name:str) -> dict:
    ''' Loads a path data (dictionary) from a json file. '''
    
    with open(os.path.join(path, file_name), 'r') as file:
        stored_data = json.load(file)

    return stored_data

# directory related functions
def get_documents_folder() -> str:
    ''' Finds the documents path inside the user's home directory. '''
    documents_path = os.path.join(str(Path.home()), 'Documents')
    return documents_path

def path_exists(file_path: str) -> bool:
    ''' Checks if a path or file path exists. '''
    return os.path.exists(file_path)
    

