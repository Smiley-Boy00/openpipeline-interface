import argparse

from .core import config
from .core.context import ProjContext

def main():
    parser = argparse.ArgumentParser(prog='openpipeline', 
                                     description='OpenPipeline Interface')

    parser.add_argument('command', nargs='?', default='info', choices=['info', 'test-assets'])

    args = parser.parse_args() # retrieve chosen command
    command_to_use = args.command

    # load project config
    config_data = config.load_config()
    if not config_data:
        parser.error('Missing Project Data.')

    sandbox = ProjContext(config_data)

    if command_to_use == 'info':
        print(f'OpenPipeline Interface {sandbox.version}')
        print(f'Project: {sandbox.name}')
        print(f'Root: {sandbox.root}')

    if command_to_use == 'test-assets':
        print('run text file')