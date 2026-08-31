# module for setting up maya tool packages
import importlib

TOOL_REGISTRY = {'mtou': 'openpipeline.opmaya.mtou'}

def launch(tool:str):
    if tool == 'mtou':
        maya_tool = importlib.import_module(TOOL_REGISTRY[tool])
        importlib.reload(maya_tool)
        maya_tool.load()

    if tool == 'creativeSK':
        from openpipeline.opmaya import creativeSkeletons
        creativeSkeletons.skeletonBuilderUI.show_skeletonBuilderUI_widget()