'''
Minimal VLC client for AceProxy. Messages class.
'''

class VlcMessage:
  class request:
    SHUTDOWN = 'shutdown'
    
    
    @staticmethod
    def startBroadcast(stream_name, input, out_port, muxer = 'ts'):
      return 'new "' + stream_name + '" broadcast input "' + input + '" output #http{mux=' + muxer + ',dst=:' + \
	str(out_port) + '/' + stream_name + '} enabled' + "\r\n" + 'control "' + stream_name + '" play'
	    
    @staticmethod    
    def stopBroadcast(stream_name):
      return 'del "' + stream_name + '"'
    
    @staticmethod
    def pauseBroadcast(stream_name):
      return 'control "' + stream_name + '" pause'
    
    @staticmethod
    def unPauseBroadcast(stream_name):
      return 'control "' + stream_name + '" play'
    
  class response:
    WRONGPASS = 'Wrong password'
    AUTHOK = 'Welcome, Master'
    BROADCASTEXISTS = 'Name already in use'
    SYNTAXERR = 'Wrong command syntax'
    STARTOK = 'new'
    STOPOK = 'del'
    STOPERR = 'media unknown'
    SHUTDOWN = 'Bye-bye!'