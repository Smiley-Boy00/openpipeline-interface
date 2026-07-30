import argparse

from .core import config
from .core.context import ProjContext

def main():
    parser = argparse.ArgumentParser(prog='openpipeline', 
                                     description='OpenPipeline Interface')

    parser.add_argument('command', nargs='?', default='info', choices=['info', 'test-assets'])
    
    parser.add_argument('--project', '-p',
                        default='opi_sandbox',
                        help='Project directory name')

    args = parser.parse_args() # retrieve chosen command
    command_to_use = args.command

    # load project config
    config_data = config.load_config(args.project)
    if not config_data:
        parser.error('Missing Project Data.')

    sandbox = ProjContext(config_data)

    if command_to_use == 'info':
        show_project_info(sandbox)

    if command_to_use == 'test-assets':
        tester_run(sandbox)

def show_project_info(project:ProjContext):
    print(f'OpenPipeline Interface {project.version}')
    print(f'Project: {project.name}')
    print(f'Root: {project.root}')

def tester_run(project:ProjContext):
    print('run text file')
    if project.assets:
        test_file = project.assets / 'my_sandbox'

    with test_file.open() as file:
        print(file.read())