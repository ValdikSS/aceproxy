'''
AceProxy: Ace Stream to HTTP Proxy

Website: https://github.com/ValdikSS/AceProxy
'''
import gevent.monkey
# Monkeypatching and all the stuff
gevent.monkey.patch_all()
import gevent.queue, logging, aceclient, BaseHTTPServer, SocketServer, urllib2
#greenlet
from aceconfig import AceConfig

class AceHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  
  def die_with_error(self):
    '''
    Close connection with error
    '''
    logging.warning("Dying with error")
    self.send_error(500)
    self.end_headers()
    self.wfile.close()
    
  def proxyReadWrite(self):
    '''
    Read video stream and send it to client
    '''
    logger = logging.getLogger('http_proxyReadWrite')
    logger.debug("Started")
    while True:
      try:
	if AceConfig.videoobey:
	  # Wait for PlayEvent if videoobey is enabled
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
    logger = logging.getLogger('http_hangDetector')
    logger.debug("Started")
    try:
      while True:
	logger.debug("PING...")
	if not self.rfile.read():
	  break
    except:
      pass
    finally:
      logger.debug("Client disconnected, destroying AceClient...")
      self.ace.destroy()
      return
	
	
  def do_GET(self):
    '''
    GET request handler
    '''
    logger = logging.getLogger('http_AceHandler')
    try:
      # If first parameter is 'pid' or 'torrent', and second parameter exists
      if not self.path.split('/')[1].lower() in ('pid', 'torrent') or not self.path.split('/')[2]:
	self.die_with_error()
	return
    except IndexError:
      self.die_with_error()
      return
    
    
    # Pretend to work fine with Fake UAs
    if AceConfig.fakeuas in self.headers.get('User-Agent'):
      logger.debug("Got fake UA: " + self.headers.get('User-Agent'))
      # Return 200 and exit
      self.send_response(200)
      self.end_headers()
      self.wfile.close()
      return
    
    # Creating AceClient
    try:
      self.ace = aceclient.AceClient(AceConfig.acehost, AceConfig.aceport, debug=AceConfig.debug)
      logger.debug("AceClient created")
    except aceclient.AceException as e:
      logger.error("AceClient create exception. ERROR: " + str(e))
      self.die_with_error()
      return
    
    try:
      # Initializing AceClient
      self.ace.aceInit(product_key = AceConfig.acekey, pause_delay = AceConfig.videopausedelay)
      logger.debug("AceClient inited")
      self.hanggreenlet = gevent.spawn(self.hangDetector)
      logger.debug("hangDetector spawned")
      
      logger.debug("Executing START")
      self.ace.START(self.path.split('/')[1].lower(), urllib2.unquote(self.path.split('/')[2]))
      logger.debug("START done")
      
      # Getting URL
      self.url = self.ace.getUrl()
      logger.debug("Got url " + self.url)
    
      # Sending client headers to videostream
      self.video = urllib2.Request(self.url)
      for key in self.headers.dict:
	self.video.add_header(key, self.headers.dict[key])
	
      self.video = urllib2.urlopen(self.video)
      # Sending client response
      self.send_response(self.video.getcode())
      logger.debug("Response sent")
      # Sleeping videodelay
      gevent.sleep(AceConfig.videodelay)
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
      
      # End headers. Next goes video data
      self.end_headers()
      logger.debug("Headers sent")
      
      # Spawning proxyReadWrite greenlet
      self.proxyReadWritegreenlet = gevent.spawn(self.proxyReadWrite)
      
      # Waiting until proxyReadWrite() ends
      self.proxyReadWritegreenlet.join()
      logger.debug("proxyReadWrite joined")
      self.hanggreenlet.join()
      logger.debug("hangDetector joined")
      
    except aceclient.AceException as e:
      logger.error("AceClient exception: " + str(e))
      self.die_with_error()
    except urllib2.URLError as e:
      logger.error("urllib2 exception: " + str(e))
      self.die_with_error()
    finally:
      logger.debug("END REQUEST")
      self.ace.destroy()
      
      
class AceServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
  pass

server = AceServer((AceConfig.httphost, AceConfig.httpport), AceHandler)
logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s', datefmt='%d.%m.%Y %H:%M:%S', level=AceConfig.httpdebug)
logger = logging.getLogger('HTTP')

try:
  logger.info("Server started.")
  server.serve_forever()
except KeyboardInterrupt:
  logger.info("Stopping server...")
  server.shutdown()
  server.server_close()
