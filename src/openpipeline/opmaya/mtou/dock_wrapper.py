# from .main_ui import mtouExporterUI as mtouUI
from . import main_ui
import importlib

## insert code to make mtou ui dockable inside maya

def load():
    # load mtou ui
    # mtouUI()
    importlib.reload(main_ui)
    main_ui.mtouExporterUI()