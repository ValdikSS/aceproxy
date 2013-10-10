'''
AceProxy configuration script
'''
import logging, platform
from aceclient.acemessages import AceConst

class AceConfig(object):
  # Ace program key (None uses remote key generator)
  acekey = None
  # Ace Stream Engine host
  acehost = '127.0.0.1'
  # Ace Stream Engine port (autodetect for Windows)
  aceport = 62062
  # Ace Stream age parameter (LT_13, 13_17, 18_24, 25_34, 35_44, 45_54, 55_64, GT_65)
  aceage = AceConst.AGE_18_24
  # Ace Stream sex parameter (MALE or FEMALE)
  acesex = AceConst.SEX_MALE
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
  # VLC muxer. You probably want one of these streamable muxers:
  # ts, asf, flv, ogg, mkv
  # You can use ffmpeg muxers too, if your VLC is built with it
  # ffmpeg{mux=NAME} (i.e. ffmpeg{mux=mpegts})
  # 
  # VLC's ts muxer sometimes can work bad, but that's the best choice for now.
  vlcmux = 'ts{use-key-frames}'
  # Force ffmpeg INPUT demuxer in VLC. Sometimes can help.
  vlcforceffmpeg = False
  # VLC debug level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  vlcdebug = logging.DEBUG
  
  # ------------------------
  # Better not to play with these in non-VLC mode!
  # Set to 0, False, 0 for best performance in VLC mode.
  
  # Stream start delay for dumb players (in seconds)
  videodelay = 2
  # Obey PAUSE and RESUME commands (stops sending data to client, should prevent annoying buffering)
  videoobey = True
  # Stream send delay after PAUSE/RESUME commands (works only if option above is enabled)
  videopausedelay = 3
  # Delay before closing Ace Stream connection when client disconnects
  videodestroydelay = 3
  # Pre-buffering timeout
  videotimeout = 40
  # ------------------------
  
  # Fake User-Agents (not video players) which generates a lot of requests
  # which Ace stream handles badly. Send them 200 OK and do nothing.
  fakeuas = ('Mozilla/5.0 IMC plugin Macintosh', )
  # User-Agents with fast and non-configurable timeout, for which we send
  # fake headers right after the connection initiated
  fakeheaderuas = ('HLS Client/2.0 (compatible; LG NetCast.TV-2012)',
		   'Mozilla/5.0 (DirectFB; Linux armv7l) AppleWebKit/534.26+ (KHTML, like Gecko) Version/5.0 Safari/534.26+ LG Browser/5.00.00(+mouse+3D+SCREEN+TUNER; LGE; 42LM670T-ZA; 04.41.03; 0x00000001;); LG NetCast.TV-2012 0'
		   )
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
