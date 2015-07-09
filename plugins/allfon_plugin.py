'''
Allfon.tv Playlist Downloader Plugin
http://ip:port/allfon
'''
import re
import logging
import urllib2
import time
from modules.PluginInterface import AceProxyPlugin
from modules.PlaylistGenerator import PlaylistGenerator
import config.allfon as config


class Allfon(AceProxyPlugin):

    # ttvplaylist handler is obsolete
    handlers = ('allfon',)

    logger = logging.getLogger('plugin_allfon')
    playlist = None
    playlisttime = None

    def __init__(self, AceConfig, AceStuff):
        pass

    def downloadPlaylist(self):
        try:
            Allfon.logger.debug('Trying to download playlist')
            print(config.url)
            req = urllib2.Request(config.url, headers={'User-Agent' : "Magic Browser"})
            Allfon.playlist = urllib2.urlopen(
                req, timeout=10).read()
            Allfon.playlisttime = int(time.time())
        except:
            Allfon.logger.error("Can't download playlist!")
            return False

        return True

    def handle(self, connection):
        # 30 minutes cache
        if not Allfon.playlist or (int(time.time()) - Allfon.playlisttime > 30 * 60):
            if not self.downloadPlaylist():
                connection.dieWithError()
                return

        hostport = connection.headers['Host']

        connection.send_response(200)
        connection.send_header('Content-Type', 'application/x-mpegurl')
        connection.end_headers()

        # Match playlist with regexp

        matches = re.finditer(r'\#EXTINF\:0\,ALLFON\.TV (?P<name>\S.+)\n.+\n.+\n(?P<url>^acestream.+$)',
                              Allfon.playlist, re.MULTILINE)
        
        add_ts = False
        try:
            if connection.splittedpath[2].lower() == 'ts':
                add_ts = True
        except:
            pass
                

        playlistgen = PlaylistGenerator()
        for match in matches:
            playlistgen.addItem(match.groupdict())

        connection.wfile.write(playlistgen.exportm3u(hostport, add_ts=add_ts))
