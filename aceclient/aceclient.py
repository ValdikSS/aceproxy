from acemessages import *
import telnetlib, logging

from gevent import monkey
monkey.patch_all()

import gevent
from gevent.event import AsyncResult
from gevent.event import Event
import greenlet


class AceException(Exception):
  '''
  Exception from AceClient
  '''
  def __init__(self, val):
    self.val = val
  def __str__(self):
    return repr(self.val)


class AceClient:
  def __init__(self, host, port, connect_timeout = 5, debug = logging.ERROR):
    # Receive buffer
    self._recvbuffer = None
    # Stream URL
    self._url = None
    # Ace stream socket
    self._socket = None
    # Shutting down flag
    self._shuttingDown = Event()
    # Product key
    self._product_key = None
    # Debug level
    self._debug = debug
    # Current STATUS
    self._status = None
    # Current STATE
    self._state = None
    # Current AUTH
    self._auth = None
    self._gender = None
    self._age = None
    # Result (Created with AsyncResult() on call)
    self._result = AsyncResult()
    self._authevent = Event()
    # Result for getURL()
    self._urlresult = AsyncResult()
    self._resumeevent = Event()
    
    
    # Logging init
    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s', datefmt='%d.%m.%Y %H:%M:%S', level=self._debug)
    logger = logging.getLogger('AceClient_init')
    
    try:
      self._socket = telnetlib.Telnet(host, port, connect_timeout)
      logger.debug("Successfully connected with Ace!")
    except Exception as e:
      raise AceException("Socket creation error! Ace is not running? " + str(e))
    
    gevent.spawn(self._recvData)
    gevent.sleep()
    
    
  def __del__(self):
    self.destroy()
    
    
  def destroy(self):
    logger = logging.getLogger("ace_destroy")
    self._resumeevent.set()
    self._urlresult.set()
    if self._shuttingDown.isSet():
      # Already in the middle of destroying
      return
    if self._socket:
      try:
	logger.debug("Destroying client...")
	self._write(AceMessage.request.SHUTDOWN)
	self._shuttingDown.set()
      except:
	# Ignore exceptions on destroy
	pass
    
  def _write(self, message):
      try:
	self._socket.write(message + "\r\n")
      except EOFError as e:
	raise AceException("Write error! " + str(e))
    
    
  def aceInit(self, gender = AceConst.SEX_MALE, age = AceConst.GENDER_18_24, product_key = None, pause_delay = 0):
    self._product_key = product_key
    self._gender = gender
    self._age = age
    self._pausedelay = pause_delay
    self._write(AceMessage.request.HELLO)
    if not self._authevent.wait(5):
      logging.error("aceInit event timeout. Wrong key?")
      return
    if not self._auth:
      logging.error("aceInit auth error. Wrong key?")
      return
    logging.debug("aceInit ended")
    
  def START(self, datatype, value):
    self._result = AsyncResult()
    self._urlresult = AsyncResult()
    
    if datatype.lower() == 'pid':
      self._write(AceMessage.request.START('PID', {'content_id': value}))
    elif datatype.lower() == 'torrent':
      self._write(AceMessage.request.START('TORRENT', {'url': value}))
      
    if not self._result.get():
      raise AceException("START error!")
    return
  
  
  def getUrl(self):
    res = self._urlresult.get()
    if res:
      return res
    else:
      return False
  
  
  def getPlayEvent(self):
    self._resumeevent.wait()
    return
    
    
  def _recvData(self):
    logger = logging.getLogger('AceClient_recvdata')

    while True:
      gevent.sleep()
      if self._shuttingDown.isSet():
	logger.debug("Shutting down is in the process, returning from _recvData...")
	self._socket.close()
	return
      
      try:
	self._recvbuffer = self._socket.read_until("\r\n", 1)
      except Exception as e:
	if self._shuttingDown.isSet():
	  logger.debug("Shutting down is in the process, returning from _recvData after socket_read...")
	else:
	  raise e
	
	
      # Parsing everything
      if self._recvbuffer.startswith(AceMessage.response.HELLO):
	# Parse HELLO
	if 'key=' in self._recvbuffer:
	  self._request_key = self._recvbuffer.split()[2].split('=')[1]
	  self._write(AceMessage.request.READY_key(self._request_key, self._product_key))
	  self._request_key = None
	else:
	  self._write(AceMessage.request.READY_nokey)
	
      elif self._recvbuffer.startswith(AceMessage.response.NOTREADY):
	# NOTREADY
	# Not implemented yet
	logger.error("Ace is not ready. Wrong auth?")
	pass
      
      elif self._recvbuffer.startswith(AceMessage.response.START):
	# START
	try:
	  self._url = self._recvbuffer.split()[1]
	  self._urlresult.set(self._url)
	  self._resumeevent.set()
	except IndexError as e:
	  self._url = None
	
      elif self._recvbuffer.startswith(AceMessage.response.STOP):
	pass
      
      elif self._recvbuffer.startswith(AceMessage.response.SHUTDOWN):
	self.destroy()
	return
	
      elif self._recvbuffer.startswith(AceMessage.response.AUTH):
	try:
	  self._auth = self._recvbuffer.split()[1]
	  # Send USERDATA here
	  self._write(AceMessage.request.USERDATA(self._gender, self._age))
	except:
	  pass
	self._authevent.set()
	
      elif self._recvbuffer.startswith(AceMessage.response.GETUSERDATA):
	raise AceException("You should init me first!")
      
      elif self._recvbuffer.startswith(AceMessage.response.STATE):
	self._state = self._recvbuffer.split()[1]
	
      elif self._recvbuffer.startswith(AceMessage.response.STATUS):
	self._tempstatus = self._recvbuffer.split()[1].split(';')[0]
	if self._tempstatus != self._status:
	  self._status = self._tempstatus
	  logger.debug("STATUS changed to "+self._status)
	if self._status == 'main:err':
	  logger.warning(self._status + ' with message ' + self._recvbuffer.split(';')[2])
	  self._result.set(False)
	  self._urlresult.set(False)
	if self._status == 'main:starting':
	  self._result.set(True)
	  
      elif self._recvbuffer.startswith(AceMessage.response.PAUSE):
	logger.debug("PAUSE event")
	self._resumeevent.clear()
	
      elif self._recvbuffer.startswith(AceMessage.response.RESUME):
	logger.debug("RESUME event")
	gevent.sleep(self._pausedelay)
	self._resumeevent.set()