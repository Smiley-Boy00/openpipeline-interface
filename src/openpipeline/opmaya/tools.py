# module for setting up maya tool packages
import importlib

TOOL_REGISTRY = {'mtou': 'openpipeline.opmaya.mtou'}

def load(tool:str):
    if tool == 'mtou':
        maya_tool = importlib.import_module(TOOL_REGISTRY[tool])
        importlib.reload(maya_tool)
        maya_tool.load()
