'''
Minimal Ace Stream client library to use with HTTP Proxy
'''

import hashlib, platform, urllib2

class AceConst:
  APIVERSION = 3
  
  GENDER_LT_13 = 1
  GENDER_13_17 = 2
  GENDER_18_24 = 3
  GENDER_25_34 = 4
  GENDER_35_44 = 5
  GENDER_45_54 = 6
  GENDER_55_64 = 7
  GENDER_GT_65 = 8
  
  SEX_MALE = 1
  SEX_FEMALE = 2
  
  STATE = {0: 'IDLE',
	     1: 'PREBUFFERING',
	     2: 'DOWNLOADING',
	     3: 'BUFFERING',
	     4: 'COMPLETED',
	     5: 'CHECKING',
	     6: 'ERROR'
	     }


class AceMessage:
  class request:
    # Requests (from client to acestream)
     # API Version
    HELLO = 'HELLOBG version=' + str(AceConst.APIVERSION) # Hello
    READY_nokey = 'READY' # Sent when ready
    STOP = 'STOP'
    SHUTDOWN = 'SHUTDOWN'
    
    @staticmethod
    def READY_key(request_key, product_key):
      if product_key:
	# If product_key is set, use it
	return 'READY key=' + product_key.split('-')[0] + '-' + \
	  hashlib.sha1(request_key + product_key).hexdigest()
      else:
	# Use site with key generator
	return 'READY key=' + urllib2.urlopen("http://valdikss.org.ru/tv/key.php?key=" + request_key).read()
    # End READY_KEY
    
    @staticmethod
    def LOADASYNC(command, request_id, params_dict):
      if command == 'TORRENT':
	return 'ASYNCLOAD ' + request_id + 'TORRENT ' + str(params_dict.get('url')) + ' ' +  \
		str(params_dict.get('developer_id', '0')) + ' ' + \
		str(params_dict.get('affiliate_id', '0')) + ' ' + \
		str(params_dict.get('zone_id', '0'))
		
      elif command == 'INFOHASH':
	return 'ASYNCLOAD ' + request_id + 'INFOHASH ' + str(params_dict.get('infohash')) + ' ' + \
		str(params_dict.get('developer_id', '0')) + ' ' + \
		str(params_dict.get('affiliate_id', '0')) + ' ' + \
		str(params_dict.get('zone_id', '0'))
		
      elif command == 'RAW':
	return 'ASYNCLOAD ' + request_id + 'RAW ' + str(params_dict.get('data')) + ' ' + \
		str(params_dict.get('developer_id', '0')) + ' ' + \
		str(params_dict.get('affiliate_id', '0')) + ' ' + \
		str(params_dict.get('zone_id', '0'))
		
      elif command == "PID":
	return 'ASYNCLOAD ' + request_id + 'PID ' + str(params_dict.get('content_id'))
    # End LOADASYNC
      
    @staticmethod
    def START(command, params_dict):
      if command == 'TORRENT':
	return 'START TORRENT ' + str(params_dict.get('url')) + ' ' + \
		str(params_dict.get('file_indexes', '0')) + ' ' + \
		str(params_dict.get('developer_id', '0')) + ' ' + \
		str(params_dict.get('affiliate_id', '0')) + ' ' + \
		str(params_dict.get('zone_id', '0')) + ' ' + \
		str(params_dict.get('stream_id', '0'))
		
      elif command == 'INFOHASH':
	return 'START INFOHASH ' + str(params_dict.get('infohash')) + ' ' + \
		str(params_dict.get('file_indexes', '0')) + ' ' + \
		str(params_dict.get('developer_id', '0')) + ' ' + \
		str(params_dict.get('affiliate_id', '0')) + ' ' + \
		str(params_dict.get('zone_id', '0')) + ' ' + \
		str(params_dict.get('stream_id', '0'))
		
      elif command == 'PID':
	return 'START PID ' + str(params_dict.get('content_id')) + ' ' + \
		str(params_dict.get('file_indexes', '0'))
		
      elif command == 'RAW':		
	return 'START RAW ' + str(params_dict.get('data')) + ' ' + \
		str(params_dict.get('file_indexes', '0')) + ' ' + \
		str(params_dict.get('developer_id', '0')) + ' ' + \
		str(params_dict.get('affiliate_id', '0')) + ' ' + \
		str(params_dict.get('zone_id', '0'))
		
      elif command == 'URL':
	return 'START URL ' + str(params_dict.get('direct_url')) + ' ' + \
		str(params_dict.get('file_indexes', '0')) + ' ' + \
		str(params_dict.get('developer_id', '0')) + ' ' + \
		str(params_dict.get('affiliate_id', '0')) + ' ' + \
		str(params_dict.get('zone_id', '0'))
		
      elif command == 'EFILE':
	return 'START EFILE ' + str(params_dict.get('efile_url'))
    # End START
    
    @staticmethod
    def GETCID(checksum, infohash, developer, affiliate, zone):
      return 'GETCID checksum=' + str(checksum) + ' infohash=' + str(infohash) + ' developer=' + \
	str(developer) + ' affiliate=' + str(affiliate) + ' zone=' + str(zone)
    
    @staticmethod
    def USERDATA(gender, age):
      return 'USERDATA [{"gender": ' + str(gender) + '}, {"age": '+ str(age) + '}]'
  
  
  class response:
    # Responses (from acestream to client)
    HELLO =		'HELLOTS' # Just the beginning
    NOTREADY =		'NOTREADY'
    START =		'START'
    STOP =		'STOP'
    SHUTDOWN =		'SHUTDOWN'
    AUTH =		'AUTH'
    GETUSERDATA =	'EVENT getuserdata'
    STATE =		'STATE'
    STATUS =		'STATUS'
    PAUSE =		'PAUSE'
    RESUME =		'RESUME'
