'''
Raketa-tv.com Playlist Downloader Plugin
Original code by tohm
http://ip:port/raketatv
'''
import re
import logging
import urllib2
import cookielib
import random
import time
import json
from base64 import b64decode
from PluginInterface import AceProxyPlugin
import raketatv_config


class Raketatv(AceProxyPlugin):
    handlers = ('raketatv', )

    logger = logging.getLogger('plugin_raketatv')
    url = raketatv_config.url
    host = raketatv_config.host
    tokenurl = 'https://raketa-tv.com/connect'
    loginurl = 'https://raketa-tv.com/login_check'
    watchurl = 'http://raketa-tv.com/watch'
    playlist = None
    playlisttime = None

    def downloadPlaylist(self):
        try:
            Raketatv.logger.debug('Trying to download playlist')
            playlist = urllib2.urlopen(Raketatv.url, timeout=10).read()
            playlisttime = int(time.time())
        except Exception as e:
            Raketatv.logger.error("Can't download playlist! " + repr(e))
            return False

        try:
            jsonplaylist = json.loads(playlist)['channels']
            playlist = "#EXTM3U\n"
            for channel in jsonplaylist:
                title = channel['title'].encode('utf-8')
                pid = channel['id'].replace('|', 'M').replace('?', 'L')
                pid = b64decode(pid)
                playlist += '#EXTINF:-1,' + title + "\n" + pid + "\n"

            Raketatv.playlist = playlist
            Raketatv.playlisttime = playlisttime
        except Exception as e:
            Raketatv.logger.error("Can't parse playlist! " + repr(e))
            return False

        return True

    def handle(self, connection):
        if not Raketatv.playlist or (int(time.time()) - Raketatv.playlisttime > 60 * 60):
            if not self.downloadPlaylist():
                connection.dieWithError()
                return

        if Raketatv.host:
            hostport = Raketatv.host + ':' + str(connection.request.getsockname()[1])
        else:
            hostport = connection.request.getsockname()[0] + ':' + str(connection.request.getsockname()[1])

        try:
            if connection.splittedpath[2].lower() == 'ts':
                # Adding ts:// after http:// for some players
                hostport = 'ts://' + hostport
        except:
            pass

        connection.send_response(200)
        connection.send_header('Content-type', 'application/x-mpegurl')
        connection.end_headers()
        connection.wfile.write(re.sub('([0-9a-f]{40})', 'http://' + hostport + '/pid/\\1', Raketatv.playlist))
