from acemessages import *

from gevent import monkey
monkey.patch_all()

import telnetlib, logging

import gevent
from gevent.event import AsyncResult
from gevent.event import Event


class AceException(Exception):
  '''
  Exception from AceClient
  '''
  def __init__(self, val):
    self.val = val
  def __str__(self):
    return repr(self.val)


class AceClient:
  def __init__(self, host, port, connect_timeout = 5, result_timeout = 5, debug = logging.ERROR):
    # Receive buffer
    self._recvbuffer = None
    # Stream URL
    self._url = None
    # Ace stream socket
    self._socket = None
    # Result timeout
    self._resulttimeout = result_timeout
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
    # Event for resuming from PAUSE
    self._resumeevent = Event()
    
    # Logger
    logger = logging.getLogger('AceClient_init')
    
    try:
      self._socket = telnetlib.Telnet(host, port, connect_timeout)
      logger.debug("Successfully connected with Ace!")
    except Exception as e:
      raise AceException("Socket creation error! Ace is not running? " + str(e))
    
    # Spawning recvData greenlet
    gevent.spawn(self._recvData)
    gevent.sleep()
    
    
  def __del__(self):
    # Destructor just calls destroy() method
    self.destroy()
    
    
  def destroy(self):
    '''
    AceClient Destructor
    '''
    if self._shuttingDown.isSet():
    # Already in the middle of destroying
      return
    
    # Logger
    logger = logging.getLogger("AceClient_destroy")
    # We should resume video to prevent read greenlet deadlock
    self._resumeevent.set()
    # And to prevent getUrl deadlock
    self._urlresult.set()

    # If socket is still alive (connected)
    if self._socket:
      try:
	logger.debug("Destroying client...")
	self._write(AceMessage.request.SHUTDOWN)
	self._shuttingDown.set()
      except:
	# Ignore exceptions on destroy
	pass
      
  def _write(self, message):
    # Return if in the middle of destroying
    if self._shuttingDown.isSet():
      return
    
    try:
      self._socket.write(message + "\r\n")
    except EOFError as e:
      raise AceException("Write error! " + str(e))
    
    
  def aceInit(self, gender = AceConst.SEX_MALE, age = AceConst.GENDER_18_24, product_key = None, pause_delay = 0):
    self._product_key = product_key
    self._gender = gender
    self._age = age
    # PAUSE/RESUME delay
    self._pausedelay = pause_delay
    
    # Logger
    logger = logging.getLogger("AceClient_aceInit")
    
    # Sending HELLO
    self._write(AceMessage.request.HELLO)
    if not self._authevent.wait(self._resulttimeout):
      logger.error("aceInit event timeout. Wrong key?")
      raise AceException("aceInit event timeout. Wrong key?")
      return
    
    if not self._auth:
      logger.error("aceInit auth error. Wrong key?")
      raise AceException("aceInit auth error. Wrong key?")
      return
    
    logger.debug("aceInit ended")
    
    
  def START(self, datatype, value):
    '''
    Start video method
    '''
    
    # Logger
    logger = logging.getLogger("AceClient_START")
    
    self._result = AsyncResult()
    self._urlresult = AsyncResult()
    
    if datatype.lower() == 'pid':
      self._write(AceMessage.request.START('PID', {'content_id': value}))
    elif datatype.lower() == 'torrent':
      self._write(AceMessage.request.START('TORRENT', {'url': value}))
      
    try:
      if not self._result.get(timeout = self._resulttimeout):
	logger.error("START error!")
	raise AceException("START error!")
    except gevent.Timeout:
      logger.error("START timeout!")
      raise AceException("START timeout!")
  
  
  def getUrl(self, timeout = 40):
    # Logger
    logger = logging.getLogger("AceClient_getURL")
    
    try:
      res = self._urlresult.get(timeout = timeout)
      return res
    except gevent.Timeout:
      logger.error("getURL timeout!")
      raise AceException("getURL timeout!")
      
  
  def getPlayEvent(self):
    '''
    Blocking while in PAUSE, non-blocking while in RESUME
    '''
    self._resumeevent.wait()
    return
    
    
  def _recvData(self):
    '''
    Data receiver method for greenlet
    '''
    logger = logging.getLogger('AceClient_recvdata')

    while True:
      gevent.sleep()
      if self._shuttingDown.isSet():
	logger.debug("Terminating")
	self._socket.close()
	return
      
      try:
	self._recvbuffer = self._socket.read_until("\r\n", 1)
      except:
	# If something happened during read, abandon reader
	# Should not ever happen
	logger.error("Exception at socket read")
	
	
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
	return
      
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