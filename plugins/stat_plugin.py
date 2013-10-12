'''
Simple statistics plugin

To use it, go to http://127.0.0.1:8000/stat
'''
from PluginInterface import AceProxyPlugin

class Stat(AceProxyPlugin):
  handlers = ('stat', )
  
  def __init__(self, AceConfig, AceStuff):
    self.config = AceConfig
    self.stuff = AceStuff
    
  def handle(self, connection):
    connection.send_response(200)
    connection.send_header('Content-type', 'text/html')
    connection.end_headers()
    connection.wfile.write('<html><body><h4>Connected clients: ' + str(sum(self.stuff.clientcounter.clients.values())) + '</h4>')
    for i in self.stuff.clientcounter.clients:
      connection.wfile.write(str(i) + ' : ' + str(self.stuff.clientcounter.clients[i]) + '<br>')
    connection.wfile.write('</body></html>')