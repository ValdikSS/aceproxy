'''
P2pProxy plugin configuration file

What is this plugin for?
 It repeats the behavior of p2pproxy to support programs written for using p2pproxy

 Some of examples for what you can use this plugin:
    Comfort TV widget (++ version)
    Official TorrentTV widget for Smart TV
    Kodi (XBMC) p2pproxy pvr plugin
    etc...

!!! It requires some changes in aceconfig.py:
    set the httpport to 8081
    set the vlcoutport to some other port (8082 for example)
'''
__author__ = 'miltador'

# Insert your email on torrent-tv.ru here
email = 're.place@me'

# Insert your torrent-tv account password
password = 'ReplaceMe'

# Update session every N minutes to prevent
# torrent-tv tracker forgetting us.
#
# 0 = disabled
# Do not touch this if you don't understand what it does!
updateevery = 60