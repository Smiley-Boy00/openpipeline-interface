
from . import main_ui
import importlib

## insert code to make mtou ui dockable inside maya

def load(*args):
    # load mtou ui
    # mtouUI()
    importlib.reload(main_ui)
    main_ui.mtouExporterUI()