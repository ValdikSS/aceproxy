'''
Minimal VLC client for AceProxy. Messages class.
'''

class VlcMessage:
  class request:
    SHUTDOWN = 'shutdown'
    
    
    @staticmethod
    def startBroadcast(stream_name, input, out_port):
      return 'new ' + stream_name + ' broadcast input "' + input + '" output #http{mux=ts,dst=:' + str(out_port) + '/' + stream_name + '} enabled' + \
	      "\r\n" + 'control ' + stream_name + ' play'
	    
    @staticmethod    
    def stopBroadcast(stream_name):
      return 'del ' + stream_name
    
    @staticmethod    
    def checkBroadcast(stream_name):
      return 'new ' + stream_name
    
  class response:
    WRONGPASS = 'Wrong password'
    AUTHOK = 'Welcome, Master'
    BROADCASTEXISTS = 'Name already in use'
    SYNTAXERR = 'Wrong command syntax'
    STARTOK = 'new'
    STOPOK = 'del'
    STOPERR = 'media unknown'
    SHUTDOWN = 'Bye-bye!'