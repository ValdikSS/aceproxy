'''
This is the example of plugin.
Rename this file to helloworld_plugin.py to enable it.

To use it, go to http://127.0.0.1:8000/helloworld
'''
from modules.PluginInterface import AceProxyPlugin


class Helloworld(AceProxyPlugin):
    handlers = ('helloworld', )

    def __init__(self, AceConfig, AceStuff):
        pass

    def handle(self, connection):
        connection.send_response(200)
        connection.end_headers()
        connection.wfile.write(
            '<html><body><h3>Hello world!</h3></body></html>')
