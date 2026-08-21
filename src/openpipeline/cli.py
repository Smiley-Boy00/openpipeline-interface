import argparse
import platform

from pathlib import Path
from .core import config
from .core.context import ProjContext
from . import opmaya

def main():
    parser = argparse.ArgumentParser(prog='openpipeline', 
                                     description='OpenPipeline Interface')
    subparsers = parser.add_subparsers(dest='system',
                                      required=True)

    set_project_commands(subparsers)
    set_maya_commands(subparsers)

    args = parser.parse_args() # retrieve chosen command
    system_to_use = args.system

    if system_to_use == 'project':
        run_project_commands(args)
    elif system_to_use == 'maya':
        run_maya_commands(args, args.maya_command)

def show_project_info(project:ProjContext):
    print(f'OpenPipeline Interface {project.version}')
    print(f'Project: {project.name}')
    print(f'Root: {project.root}')

def tester_run(project:ProjContext):
    if project.assets:
        test_file = project.assets / 'my_sandbox.txt'

    with test_file.open() as file:
        print(file.read())

def set_project_commands(subparsers: argparse._SubParsersAction):
    project_parser: argparse.ArgumentParser = subparsers.add_parser('project',
                                                                    help='Parser for project related commands')
    
    # create command flag to run package dependent functions
    project_parser.add_argument('command', nargs='?', default='info', choices=['info',
                                                                        'test-assets'])
    
    # create flag to allow project selection/switching
    project_parser.add_argument('--project', '-p',
                        default='opi_sandbox',
                        help='Project directory name')

def set_maya_commands(subparsers: argparse._SubParsersAction):
    maya_parser: argparse.ArgumentParser = subparsers.add_parser('maya', 
                                                                 description='OpenPipeline Maya Integration',
                                                                 help='Parser for maya OPI related commands')

    maya_commands = maya_parser.add_subparsers(dest='maya_command',
                                               required=True)

    mod_parser = maya_commands.add_parser('mod')
    
    mod_parser.add_argument('--make-mod', '-m',
                             nargs='?',
                             default=None,
                             const='./src/openpipeline',
                             help='Builds maya module file. Input maya module path: "/path/to/maya/modules", ' \
                             'if no path given, it will default to "./src/openpipeline"')
    mod_parser.add_argument('--find-paths', '-f',
                             nargs=1,
                             default=None,)

def run_project_commands(args):
    command_to_use = args.command

    # load project config
    config_data = config.load_config(args.project)
    if not config_data:
        raise SystemExit('Missing Project Data.')

    sandbox = ProjContext(config_data) # load project attributes

    if command_to_use == 'info':
        show_project_info(sandbox)

    if command_to_use == 'test-assets':
        tester_run(sandbox)

def run_maya_commands(args, command):
    if command == 'mod':
        if args.make_mod:
            mod_path = Path(args.make_mod)
            opmaya.integrator.build_maya_mod(mod_path)

        if args.find_paths:
            running_os=platform.system().lower()
            opmaya.integrator.find_module_paths(os=running_os, version=args.find_mod[0])