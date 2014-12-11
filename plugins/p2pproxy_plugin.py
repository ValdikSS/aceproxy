'''
P2pProxy response simulator
Uses torrent-tv API for it's work

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
import gevent

__author__ = 'miltador'

import logging
import urllib2
import time
from xml.dom.minidom import parseString

from modules.PluginInterface import AceProxyPlugin
from modules.PlaylistGenerator import PlaylistGenerator
import config.p2pproxy


class P2pproxy(AceProxyPlugin):
    handlers = ('channels', )

    logger = logging.getLogger('plugin_p2pproxy')

    email = config.p2pproxy.email
    password = config.p2pproxy.password

    session = None

    xml = None
    translationslist = None
    categories = dict()

    playlisttime = None

    def __init__(self, AceConfig, AceStuff):
        super(P2pproxy, self).__init__(AceConfig, AceStuff)
        if config.p2pproxy.updateevery:
            gevent.spawn(self.sessionUpdater)

    def sessionUpdater(self):
        while True:
            gevent.sleep(config.p2pproxy.updateevery * 60)
            self.auth()

    '''
    Every API request returns if it is successfull and if no, gives a reason
    '''

    def checkRequestSuccess(self, res):
        success = res.getElementsByTagName('success')[0].childNodes[0].data
        if success == 0 or success is None:
            error = res.getElementsByTagName('error')[0].childNodes[0].data
            P2pproxy.logger.error('Faild to perform the torrent-tv API request, reason: ' +
                                  error)
            if error == 'incorrect':  # trying to fix
                P2pproxy.session = None
                if not self.auth():
                    return False
        return True

    '''
    Returns the current session
    '''

    def auth(self):
        try:
            P2pproxy.logger.debug('Trying to access torrent-tv API')
            xmlresult = urllib2.urlopen(
                'http://api.torrent-tv.ru/v2_auth.php?username=' + P2pproxy.email + '&password=' + P2pproxy.password +
                '&application=tsproxy&typeresult=xml', timeout=10).read()
        except:
            P2pproxy.logger.error("Can't access to API! Maybe torrent-tv is down")
            return False

        res = parseString(xmlresult).documentElement
        if self.checkRequestSuccess(res):
            P2pproxy.session = res.getElementsByTagName('session')[0].childNodes[0].data
            return True
        else:
            return False

    def getTranslations(self):
        try:
            P2pproxy.logger.debug('Trying to get the playlist from torrent-tv')
            P2pproxy.xml = urllib2.urlopen(
                'http://api.torrent-tv.ru/v2_alltranslation.php?session=' + P2pproxy.session +
                '&type=all&typeresult=xml', timeout=10).read()
        except:
            P2pproxy.logger.error("Can't access to API! Maybe torrent-tv is down")
            return False

        res = parseString(P2pproxy.xml).documentElement
        if self.checkRequestSuccess(res):
            P2pproxy.translationslist = res.getElementsByTagName('channel')
            categorieslist = res.getElementsByTagName('category')
            for cat in categorieslist:
                gid = cat.getAttribute('id')
                name = cat.getAttribute('name')
                P2pproxy.categories[gid] = name
            return True
        else:
            return False

    '''
    Gets the source for Ace Stream by channel id
    Returns type of source and source value
    '''

    def getSource(self, channelId):
        if P2pproxy.session is None:
                if not self.auth():
                    return None, None
        P2pproxy.logger.error('Getting source for channel id: ' + channelId)
        try:
            xmlresult = urllib2.urlopen(
                'http://api.torrent-tv.ru/v2_get_stream.php?session=' + P2pproxy.session +
                '&channel_id=' + channelId + '&typeresult=xml', timeout=10).read()
        except:
            P2pproxy.logger.error("Can't access to API! Maybe torrent-tv is down")
            return None, None
        res = parseString(xmlresult).documentElement
        if self.checkRequestSuccess(res):
            return res.getElementsByTagName('type')[0].childNodes[0].data, \
                   res.getElementsByTagName('source')[0].childNodes[0].data
        else:
            return None, None

    def downloadPlaylist(self):
        P2pproxy.logger.debug('Going to update p2pproxy playlist')
        # First of all, authorization and getting session
        if P2pproxy.session is None:  # we need to auth only once
            if not self.auth():
                return False

        # Now we get translations and categories lists
        if not self.getTranslations():
            return False

        P2pproxy.logger.debug('Successfully downloaded playlist through torrent-tv API')

        P2pproxy.playlisttime = int(time.time())
        return True

    def handle(self, connection):
        P2pproxy.logger.debug('Handling request')
        # 30 minutes cache
        if P2pproxy.translationslist is None or (int(time.time()) - P2pproxy.playlisttime > 30 * 60):
            if not self.downloadPlaylist():
                connection.dieWithError()
                return

        if 'm3u' in connection.path:
            hostport = connection.headers['Host']

            connection.send_response(200)
            connection.send_header('Content-Type', 'application/x-mpegurl')
            connection.end_headers()

            playlistgen = PlaylistGenerator()
            for channel in P2pproxy.translationslist:
                name = channel.getAttribute('name')
                cid = channel.getAttribute('id')
                group = P2pproxy.categories[channel.getAttribute('group')]
                playlistgen.addItem({'name': name, 'url': cid, 'group': group})

            exported = playlistgen.exportm3u(hostport, False)
            exported = exported.encode('utf-8')
            connection.wfile.write(exported)
        else:
            if P2pproxy.xml is None:
                connection.dieWithError()
                return
            connection.send_response(200)
            connection.send_header('Content-Type', 'text/xml')
            connection.end_headers()

            connection.wfile.write(P2pproxy.xml)