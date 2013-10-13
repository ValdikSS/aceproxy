'''
Torrent-tv.ru Playlist Downloader Plugin
http://ip:port/ttvplaylist
'''
import re
import logging
import urllib2
import time
from PluginInterface import AceProxyPlugin
import ttvplaylist_config


class Ttvplaylist(AceProxyPlugin):
    handlers = ('ttvplaylist', )

    logger = logging.getLogger('plugin_ttvplaylist')
    url = ttvplaylist_config.url
    host = ttvplaylist_config.host
    playlist = None
    playlisttime = None

    def downloadPlaylist(self):
        try:
            Ttvplaylist.logger.debug('Trying to download playlist')
            Ttvplaylist.playlist = urllib2.urlopen(
                Ttvplaylist.url, timeout=10).read()
            Ttvplaylist.playlisttime = int(time.time())
        except:
            Ttvplaylist.logger.error("Can't download playlist!")
            return False

        return True

    def handle(self, connection):
        if not Ttvplaylist.playlist or (int(time.time()) - Ttvplaylist.playlisttime > 60 * 60):
            if not self.downloadPlaylist():
                connection.dieWithError()
                return

        if Ttvplaylist.host:
            hostport = Ttvplaylist.host + ':' + str(connection.request.getsockname()[1])
        else:
            hostport = connection.request.getsockname()[0] + ':' + str(connection.request.getsockname()[1])

        connection.send_response(200)
        connection.send_header('Content-type', 'application/x-mpegurl')
        connection.end_headers()
        connection.wfile.write(re.sub('([0-9a-f]{40})', 'http://' + hostport + '/pid/\\1', Ttvplaylist.playlist))
