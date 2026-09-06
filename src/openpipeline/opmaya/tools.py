# module for setting up maya tool packages
import importlib

TOOL_REGISTRY = {'mtou': 'openpipeline.opmaya.mtou'}

def load(tool:str):
    maya_tool = importlib.import_module(TOOL_REGISTRY[tool])
    importlib.reload(maya_tool)
    maya_tool.load()

def unload(tool:str):
    maya_tool = importlib.import_module(TOOL_REGISTRY[tool])
    maya_tool.unload()