'''
Torrent-tv.ru Playlist Downloader Plugin configuration file
'''

# Insert your Torrent-tv.ru playlist URL here
url = ''

# TV Guide URL
tvgurl = 'http://api.torrent-tv.ru/ttv.xmltv.xml.gz'

# Shift the TV Guide time to the specified number of hours
tvgshift = 0

# Download playlist every N minutes to prevent
# torrent-tv tracker forgetting us.
#
# 0 = disabled
updateevery = 0
