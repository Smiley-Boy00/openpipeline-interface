# module for setting up maya tool packages
import importlib

from ..core.context import ProjContext


def load(registry:ProjContext, tool:str):
    maya_tool = importlib.import_module(registry.opmaya_reg[tool])
    importlib.reload(maya_tool)
    maya_tool.load()

def unload(registry:ProjContext, tool:str):
    maya_tool = importlib.import_module(registry.opmaya_reg[tool])
    maya_tool.unload()