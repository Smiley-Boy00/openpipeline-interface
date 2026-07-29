import sys

from .core import config, context

# load project config

config_data = config.load_config()

if not config_data:
    sys.stderr.write('Missing Project Data.')

sandbox_proj=context.ProjContext(config_data)
sys.stdout.write(f'OpenPipeline Interface {sandbox_proj.version}\nProject: {sandbox_proj.name}')


