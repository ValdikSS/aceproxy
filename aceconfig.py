'''
AceProxy configuration script
'''
import logging, platform

class AceConfig:
  # Ace program key (None uses remote key generator)
  acekey = None
  # Ace Stream Engine host
  acehost = '127.0.0.1'
  # Ace Stream Engine port (autodetect for Windows)
  aceport = 62062
  # AceClient debug level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  debug = logging.DEBUG
  
  # HTTP Server host
  httphost = '0.0.0.0'
  # HTTP Server port
  httpport = 8000
  
  # Enable VLC or not
  # I strongly recommend to use VLC, because it lags a lot without it
  # That's Ace Stream Engine fault.
  vlcuse = False
  # VLC host
  vlchost = '127.0.0.1'
  # VLC telnet port
  vlcport = 4212
  # VLC streaming port 
  vlcoutport = 8081
  # VLC password
  vlcpass = 'admin'
  # VLC debug level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  vlcdebug = logging.DEBUG
  
  # ------------------------
  # Better not to play with these in non-VLC mode!
  # Set to 0, False, 0 for best performance in VLC mode.
  
  # Stream start delay for dumb players (in seconds)
  videodelay = 2
  # Obey PAUSE and RESUME commands (stops sending data to client, should prevent annoying buffering)
  videoobey = True
  # Stream send delay on PAUSE/RESUME commads (works only if option above is enabled)
  videopausedelay = 3
  # Pre-buffering timeout
  videotimeout = 40
  # ------------------------
  
  # Fake User-Agents (not video players) which generates a lot of requests
  # which Ace stream handles badly. Send them 200 OK and do nothing.
  fakeuas = ('Mozilla/5.0 IMC plugin Macintosh')
  # HTTP debug level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  httpdebug = logging.DEBUG
  
  
  
  '''
  Do not touch this
  '''
  if platform.system() == 'Windows':
    import _winreg
    import os.path
    reg = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)
    key = _winreg.OpenKey(reg, 'Software\AceStream')
    value = _winreg.QueryValueEx(key, 'EnginePath')
    dirpath = os.path.dirname(value[0])
    try:
      aceport = int(open(dirpath + '\\acestream.port', 'r').read())
    except IOError:
      # Ace Stream is not running, start it
      import subprocess, time
      subprocess.Popen([value[0]])
      _started = False
      for i in xrange(10):
	time.sleep(1)
	try:
	  aceport = int(open(dirpath + '\\acestream.port', 'r').read())
	  _started = True
	  break
	except IOError:
	  _started = False
      if not _started:
	print "Can't start engine!"
	quit()
  '''
  Do not touch this
  '''
