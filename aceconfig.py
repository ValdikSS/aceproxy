'''
AceProxy configuration script
'''
import logging, platform

class AceConfig:
  # Ace program key (The default key works only with no-ads premium option)
  acekey = 'kjYX790gTytRaXV04IvC-xZH3A18sj5b1Tf3I-J5XVS1xsj-j0797KwxxLpBl26HPvWMm'
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
  vlcuse = False
  # VLC host
  vlchost = '127.0.0.1'
  # VLC port
  vlcport = 4212
  # VLC password
  vlcpass = 'admin'
  
  # ------------------------
  # Better not to use any of these with VLC
  
  # Stream start delay for dumb players (in seconds)
  videodelay = 2
  # Obey PAUSE and RESUME commands (stops sending data to client, should prevent annoying buffering)
  videoobey = True
  # Stream send delay on PAUSE/RESUME commads (works only if option above is enabled)
  videopausedelay = 3
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
    aceport = int(open(dirpath + '\\acestream.port', 'r').read())
  '''
  Do not touch this
  '''