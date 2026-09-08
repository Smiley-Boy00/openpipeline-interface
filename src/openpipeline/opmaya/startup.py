## script should be called from the opi_maya plugin script
from ..core import config
from ..core.context import ProjContext
from . import tools


def get_project():
    sandbox = ProjContext(config.load_config('opi_sandbox'))
    return sandbox

def initializer():
    print('Initializing OPI plugin.')

    for tool in get_project().opmaya_reg:
        tools.load(get_project(), tool)

def uninitializer():
    print('Deactivating OPI plugin.')

    for tool in get_project().opmaya_reg:
        tools.unload(get_project(), tool)