'''
YTV.su Playlist Downloader Plugin
http://ip:port/ytv
'''
import json
import logging
import urllib2
import time
from modules.PluginInterface import AceProxyPlugin
from modules.PlaylistGenerator import PlaylistGenerator
import config.ytv


class Ytv(AceProxyPlugin):

    handlers = ('ytv', )

    logger = logging.getLogger('plugin_ytv')
    url = config.ytv.url
    playlist = None
    playlisttime = None

    def downloadPlaylist(self):
        try:
            Ytv.logger.debug('Trying to download playlist')
            Ytv.playlist = urllib2.urlopen(
                Ytv.url, timeout=10).read()
            Ytv.playlisttime = int(time.time())
        except:
            Ytv.logger.error("Can't download playlist!")
            return False

        return True

    def handle(self, connection):
        # 30 minutes cache
        if not Ytv.playlist or (int(time.time()) - Ytv.playlisttime > 30 * 60):
            if not self.downloadPlaylist():
                connection.dieWithError()
                return

        hostport = connection.headers['Host']

        connection.send_response(200)
        connection.send_header('Content-Type', 'application/x-mpegurl')
        connection.end_headers()

        # Un-JSON channel list
        try:
            jsonplaylist = json.loads(Ytv.playlist)
        except Exception as e:
            Ytv.logger.error("Can't load JSON! " + repr(e))
            return False

        try:
            groups = dict(map(lambda item: item.values(), jsonplaylist['genres']))
            channels = jsonplaylist['channels']
        except Exception as e:
            Ytv.logger.error("Can't parse JSON! " + repr(e))
            return False

        add_ts = False
        try:
            if connection.splittedpath[2].lower() == 'ts':
                add_ts = True
        except:
            pass

        playlistgen = PlaylistGenerator()

        for channel in channels:
            groupid = channel.get('genre_id')
            if groupid and groups.get(groupid):
                channel['group'] = groups.get(groupid)
            playlistgen.addItem(channel)
        
        exported = playlistgen.exportm3u(hostport, add_ts)
        exported = exported.encode('utf-8')
        connection.wfile.write(exported)