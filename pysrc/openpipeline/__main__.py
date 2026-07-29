import sys

from .core import config, context

# load project config

config_data = config.load_config()

if not config_data:
    sys.stderr.write('Missing Project Data.')

sandbox_proj=context.ProjContext(config_data, 'Unix')
sys.stdout.write(f'OpenPipeline Interface {sandbox_proj.version}\nProject: {sandbox_proj.name}\n')
sys.stdout.write(f'Project Root: {sandbox_proj.project_root}\n')


