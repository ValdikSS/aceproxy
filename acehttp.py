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
  # Obey PAUSE and RESUME commands (should prevent annoying buffering)
  httpobey = True
  # Stream send delay on PAUSE/RESUME commads (works only if option above is enabled)
  httppausedelay = 3
  # Fake User-Agents (not video players) which generates a lot of requests
  # which Ace stream handles badly. Send them 200 OK and do nothing.
  fakeuas = ('Mozilla/5.0 IMC plugin Macintosh')
  # HTTP debug level
  httpdebug = logging.DEBUG
    

class AceHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  
  def die_with_error(self):
    logging.warning("Dying with error")
    self.send_error(500)
    self.end_headers()
    self.wfile.close()
    
  def proxyReadWrite(self):
    '''
    Read video stream and send it to client
    '''
    logger = logging.getLogger('proxyReadWrite')
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
	self.wfile.write(data)
      except:
	# Video connection dropped
	logger.debug("Video Connection dropped")
	return
	
	
  def hangDetector(self):
    '''
    Detect client disconnection while in the middle of something
    or just normal connection close.
    '''
    logger = logging.getLogger('hangDetector')
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
      if not self.path.split('/')[1].lower() in ('pid', 'torrent') or not self.path.split('/')[2]:
	self.die_with_error()
	return
    except IndexError:
      self.die_with_error()
      return
    
    try:
      if self.headers.get('User-Agent') in Ace.fakeuas:
	logger.debug("Got fake UA: " + self.headers.get('User-Agent'))
	# Return 200 and exit
	self.send_response(200)
	self.end_headers()
	self.wfile.close()
	return
	
      self.ace = aceclient.AceClient(Ace.acehost, Ace.aceport, debug=Ace.debug)
      logger.debug("Ace created")
      self.ace.aceInit(product_key = Ace.acekey, pause_delay = Ace.httppausedelay)
      logger.debug("Ace inited")
      
      self.hanggreenlet = gevent.spawn(self.hangDetector)
      logger.debug("hangDetector spawned")
      
      try:
	self.ace.START(self.path.split('/')[1].lower(), urllib2.unquote(self.path.split('/')[2]))
      except aceclient.AceException:
	self.die_with_error()
	return
	
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
    
    # Sending client headers to videostream
    self.video = urllib2.Request(self.url)
    for key in self.headers.dict:
      self.video.add_header(key, self.headers.dict[key])
    try:
      self.video = urllib2.urlopen(self.video)
      # Sending client response
      self.send_response(self.video.getcode())
      logger.debug("Response sent")
      # Sleeping httpdelay
      gevent.sleep(Ace.httpdelay)
      
    except urllib2.URLError as e:
      logger.error("Error from URLLIB: " + str(e))
      self.die_with_error()
      return
    
    logger.debug("Opened url")
    self.send_header("Connection", "Close")
    del self.video.info().dict['connection']
    del self.video.info().dict['server']
    if self.video.info().dict.get('transfer-encoding'):
      del self.video.info().dict['transfer-encoding']  
    if self.video.info().dict.get('keep-alive'):
      del self.video.info().dict['keep-alive']
    
    # Sending videostream headers to client
    for key in self.video.info().dict:
      self.send_header(key, self.video.info().dict[key])
    
    self.end_headers()
    logger.debug("Headers sent")
    
    self.proxyReadWritegreenlet = gevent.spawn(self.proxyReadWrite)
    
    # Waiting until proxyReadWrite() ends
    self.proxyReadWritegreenlet.join()
    logger.debug("proxyReadWrite joined")
    self.hanggreenlet.join()
    logger.debug("hangDetector joined")
    
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
