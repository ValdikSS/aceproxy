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
  # Ace program key
  acekey = ''
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
    try:
      self.send_error(500)
      self.end_headers()
      self.ace.destroy()
    except:
      # We shouldn't be here
      return
    
  def proxy_read(self):
    '''
    Read video stream and put its' data into a queue
    '''
    while True:
      try:
	if Ace.httpobey:
	  self.ace.getPlayEvent()
	data = self.video.read(4*1024)
	if not data:
	  #self.ace.destroy()
	  # Video connection closed
	  return
	self.buffer.put(data)
      except:
	# Connection dropped
	#self.ace.destroy()
	print "exception from read"
	return
      
    
  def proxy_write(self):
    '''
    Read video queue and write it to client
    '''
    while True:
      try:
	if not self.proxyreadgreenlet.ready():
	  if Ace.httpobey:
	    self.ace.getPlayEvent()
	  self.wfile.write(self.buffer.get())
	else:
	  # proxy_read is dead
	  return
      except:
	# Connection dropped
	#self.ace.destroy()
	return
	
  def hangdetector(self):
    '''
    Detect client disconnection while in the middle of something
    or just normal connection close.
    '''
    logger = logging.getLogger('HangDetector')
    try:
      while True:
	logger.debug("PING...")
	if not self.rfile.read():
	  break
    except:
      self.proxyreadgreenlet.kill()
      self.proxywritegreenlet.kill()
      self.rfile.close()
      self.wfile.close()
    finally:
      self.ace.destroy()
      logger.debug("Client disconnected, destroying ACE...")
      return
	
	
  def do_GET(self):
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
      
      try:
	self.ace.START(self.path.split('/')[2])
      except aceclient.AceException:
	self.die_with_error()
	return
      
      self.send_response(200)
      self.send_header("Content-Type", "video/mpeg")
      self.send_header("Accept-Ranges", "bytes")
      self.end_headers()
      
      self.buffer = gevent.queue.Queue(Ace.httpqueuelen)
      gevent.sleep(Ace.httpdelay)
	
    except aceclient.AceException as e:
      logger.error("ACE Exception while creating new instance of ace! " + str(e))
      self.die_with_error()
      return
    
    self.url = self.ace.getUrl()
    
    logger.debug("Got url " + self.url)
    try:
      self.video = urllib2.urlopen(self.url)
    except urllib2.URLError as e:
      logger.error("Error from URLLIB: " + str(e))
      self.die_with_error()
      return
    
    logger.debug("Opened url")
    
    self.proxyreadgreenlet = gevent.spawn(self.proxy_read)
    self.proxywritegreenlet = gevent.spawn(self.proxy_write)
    
    # Waiting until proxy_read() and proxy_write() ends
    self.proxyreadgreenlet.join()
    self.proxywritegreenlet.join()
    self.hanggreenlet.join()
    # If any...
    self.ace.destroy()
    
    
      
      
class AceServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
  pass

server = AceServer((Ace.httphost, Ace.httpport), AceHandler)
logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%d.%m.%Y %H:%M:%S', level=Ace.httpdebug)
logger = logging.getLogger('HTTP')

try:
  logger.info("Server started.")
  server.serve_forever()
except KeyboardInterrupt:
  logger.info("Stopping server...")
  server.shutdown()
  server.server_close()
