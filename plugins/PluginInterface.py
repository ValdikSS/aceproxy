'''
Plugin interface.
Interhit your plugins from this class.

Your plugin name should end with _plugin.py, e.g. example_plugin.py
Your class name should match plugin name and be capitalized, e.g. Example
Do not use dots in filename or class name.

See helloworld_plugin_.py for the basic plugin example.
'''


class AceProxyPlugin(object):

    def __init__(self, AceConfig, AceStuff):
        pass

    def handle(self, connection):
        raise NotImplementedError
