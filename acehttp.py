'''
AceProxy: Ace Stream to HTTP Proxy

Website: https://github.com/ValdikSS/AceProxy
'''
import gevent.monkey
# Monkeypatching and all the stuff
gevent.monkey.patch_all()
import gevent.queue
import aceclient
import logging
import BaseHTTPServer
import SocketServer
import urllib2
import platform
import greenlet

class Ace:
  # Ace program key (public no-ad key from Constantin)
  acekey = 'kjYX790gTytRaXV04IvC-xZH3A18sj5b1Tf3I-J5XVS1xsj-j0797KwxxLpBl26HPvWMm'
  # Ace Stream host
  acehost = '127.0.0.1'
  # Ace Stream port (autodetect for Windows)
  aceport = 62062
  
  if platform.system() == 'Windows':
    import _winreg
    import os.path
    reg = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)
    key = _winreg.OpenKey(reg, 'Software\AceStream')
    value = _winreg.QueryValueEx(key, 'EnginePath')
    dirpath = os.path.dirname(value[0])
    aceport = int(open(dirpath + '\\acestream.port', 'r').read())
    
  # AceClient debug level
  debug = logging.DEBUG
  # HTTP host
  httphost = '0.0.0.0'
  # HTTP port
  httpport = 8000
  # Stream start delay for dumb players (in seconds)
  httpdelay = 2
  # Stream queue size (1 = 4KB)
  httpqueuelen = 10
  # Obey PAUSE and RESUME commands (should prevent annoying buffering)
  httpobey = True
  # Stream send delay on PAUSE/RESUME commads (works only if option above is enabled)
  httppausedelay = 3
  # HTTP debug level
  httpdebug = logging.DEBUG
    

class AceHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  
  def die_with_error(self):
    logging.warning("Dying with error")
    self.send_error(500)
    self.end_headers()
    self.wfile.close()
    
  def proxy_read(self):
    '''
    Read video stream and put its' data into a queue
    '''
    logger = logging.getLogger('proxy_read')
    logger.debug("Started")
    while True:
      try:
	if Ace.httpobey:
	  self.ace.getPlayEvent()
	data = self.video.read(4*1024)
	if not data:
	  # Video connection closed
	  logger.debug("Video connection closed")
	  return
	self.buffer.put(data)
      except:
	# Video connection dropped
	logger.debug("Video Connection dropped")
	return
      
    
  def proxy_write(self):
    '''
    Read video queue and write it to client
    '''
    logger = logging.getLogger('proxy_write')
    logger.debug("Started")
    while True:
      try:
	if not self.proxyreadgreenlet.ready():
	  if Ace.httpobey:
	    self.ace.getPlayEvent()
	  self.wfile.write(self.buffer.get())
	else:
	  # proxy_read is dead
	  logger.debug("dead")
	  return
      except:
	# Client connection dropped
	logger.debug("Client connection dropped")
	return
	
  def hangdetector(self):
    '''
    Detect client disconnection while in the middle of something
    or just normal connection close.
    '''
    logger = logging.getLogger('HangDetector')
    logger.debug("Started")
    try:
      while True:
	logger.debug("PING...")
	if not self.rfile.read():
	  break
    except:
      pass
    finally:
      logger.debug("Client disconnected, destroying ACE...")
      self.ace.destroy()
      return
	
	
  def do_GET(self):
    '''
    GET request handler
    '''
    logger = logging.getLogger('AceHandler')
    try:
      if self.path.split('/')[1].lower() != 'pid' or not self.path.split('/')[2]:
	self.die_with_error()
	return
    except IndexError:
      self.die_with_error()
      return
    
    try:
      self.ace = aceclient.AceClient(Ace.acehost, Ace.aceport, debug=Ace.debug)
      logger.debug("Ace created")
      self.ace.aceInit(product_key = Ace.acekey, pause_delay = Ace.httppausedelay)
      logger.debug("Ace inited")
      
      self.hanggreenlet = gevent.spawn(self.hangdetector)
      logger.debug("hangdetector spawned")
      
      try:
	self.ace.START(self.path.split('/')[2])
      except aceclient.AceException:
	self.die_with_error()
	return
      
      self.send_response(200)
      logger.debug("Response sent")
      
      self.buffer = gevent.queue.Queue(Ace.httpqueuelen)
      gevent.sleep(Ace.httpdelay)
	
    except aceclient.AceException as e:
      logger.error("ACE Exception while creating new instance of ace! " + str(e))
      self.die_with_error()
      return
    
    logger.debug("Getting url...")
    self.url = self.ace.getUrl()
    if not self.url:
      logger.error("No URL")
      self.die_with_error()
      return      
    
    logger.debug("Got url " + self.url)
    try:
      self.video = urllib2.urlopen(self.url)
    except urllib2.URLError as e:
      logger.error("Error from URLLIB: " + str(e))
      self.die_with_error()
      return
    
    logger.debug("Opened url")
    self.send_header("Connection", "Close")
    del self.video.info().dict['connection']
    del self.video.info().dict['server']
    del self.video.info().dict['transfer-encoding']
    for key in self.video.info().dict:
      self.send_header(key, self.video.info().dict[key])
    self.end_headers()
    logger.debug("Headers sent")
    
    self.proxyreadgreenlet = gevent.spawn(self.proxy_read)
    self.proxywritegreenlet = gevent.spawn(self.proxy_write)
    
    # Waiting until proxy_read() and proxy_write() ends
    self.proxywritegreenlet.join()
    logger.debug("read_write killed")
    # proxy_read greenlet will deadlock if not killed
    self.proxyreadgreenlet.kill()
    logger.debug("read_proxy joined")
    self.hanggreenlet.join()
    logger.debug("hangdetector joined")
    
    # If any...
    self.ace.destroy()
    logger.debug("END REQUEST")
    
    
      
      
class AceServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
  pass

server = AceServer((Ace.httphost, Ace.httpport), AceHandler)
logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s', datefmt='%d.%m.%Y %H:%M:%S', level=Ace.httpdebug)
logger = logging.getLogger('HTTP')

try:
  logger.info("Server started.")
  server.serve_forever()
except KeyboardInterrupt:
  logger.info("Stopping server...")
  server.shutdown()
  server.server_close()
