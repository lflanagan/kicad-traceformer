from .netlist_action import NetlistPluginAction

# Register immediately so KiCad shows the toolbar button on load.
NetlistPluginAction().register()
