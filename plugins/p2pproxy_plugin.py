"""
P2pProxy response simulator
Uses torrent-tv API for it's work

What is this plugin for?
 It repeats the behavior of p2pproxy to support programs written for using p2pproxy

 Some of examples for what you can use this plugin:
    Comfort TV++ widget
    Official TorrentTV widget for Smart TV
    Kodi p2pproxy pvr plugin
    etc...

!!! It requires some changes in aceconfig.py:
    set the httpport to 8081
    set the vlcoutport to some other port (8082 for example)
"""
__author__ = 'miltador'

import logging
import re
import urllib2
import urlparse
from torrenttv_api import TorrentTvApi
from datetime import date

from modules.PluginInterface import AceProxyPlugin
from modules.PlaylistGenerator import PlaylistGenerator
import config.p2pproxy as config


class P2pproxy(AceProxyPlugin):
    handlers = ('channels', 'archive', 'xbmc.pvr')

    logger = logging.getLogger('plugin_p2pproxy')

    def __init__(self, AceConfig, AceStuff):
        super(P2pproxy, self).__init__(AceConfig, AceStuff)
        self.params = None

    def handle(self, connection):
        P2pproxy.logger.debug('Handling request')

        hostport = connection.headers['Host']

        query = urlparse.urlparse(connection.path).query
        self.params = urlparse.parse_qs(query)

        if connection.reqtype == 'channels':  # /channels/ branch
            if len(connection.splittedpath) == 3 and connection.splittedpath[2].split('?')[
                0] == 'play':  # /channels/play?id=[id]
                channel_id = self.get_param('id')
                if not channel_id:
                    # /channels/play?id=&_=[epoch timestamp] is Torrent-TV widget proxy check
                    # P2pProxy simply closes connection on this request sending Server header, so do we
                    if self.get_param('_'):
                        P2pproxy.logger.debug('Status check')
                        connection.send_response(200)
                        connection.send_header('Access-Control-Allow-Origin', '*')
                        connection.send_header('Connection', 'close')
                        connection.send_header('Content-Type', 'text/plain;charset=utf-8')
                        connection.send_header('Server', 'P2pProxy/1.0.3.1 AceProxy')
                        connection.wfile.write('\r\n')
                        return
                    else:
                        connection.dieWithError()  # Bad request
                        return

                stream_url = None

                session = TorrentTvApi.auth(config.email, config.password)
                stream_type, stream = TorrentTvApi.stream_source(session, channel_id)

                if stream_type == 'torrent':
                    stream_url = re.sub('^(http.+)$',
                                        lambda match: '/torrent/' + urllib2.quote(match.group(0), '') + '/stream.mp4',
                                        stream)
                elif stream_type == 'contentid':
                    stream_url = re.sub('^([0-9a-f]{40})',
                                        lambda match: '/pid/' + urllib2.quote(match.group(0), '') + '/stream.mp4',
                                        stream)
                connection.path = stream_url
                connection.splittedpath = stream_url.split('/')
                connection.reqtype = connection.splittedpath[1].lower()
                connection.handleRequest(False)
            elif self.get_param('type') == 'm3u':  # /channels/?filter=[filter]&group=[group]&type=m3u
                connection.send_response(200)
                connection.send_header('Content-Type', 'application/x-mpegurl')
                connection.end_headers()

                param_group = self.get_param('group')
                param_filter = self.get_param('filter')
                if not param_filter:
                    param_filter = 'all'  # default filter

                session = TorrentTvApi.auth(config.email, config.password)
                translations_list = TorrentTvApi.translations(session, param_filter)

                playlistgen = PlaylistGenerator()
                P2pproxy.logger.debug('Generating requested m3u playlist')
                for channel in translations_list:
                    group_id = channel.getAttribute('group')

                    if param_group and param_group != 'all' and param_group != group_id:  # filter channels by group
                        continue

                    name = channel.getAttribute('name')
                    group = TorrentTvApi.CATEGORIES[int(group_id)].decode('utf-8')
                    cid = channel.getAttribute('id')
                    logo = channel.getAttribute('logo')
                    if config.fullpathlogo:
                        logo = 'http://torrent-tv.ru/uploads/' + logo

                    playlistgen.addItem({'name': name, 'url': cid, 'group': group, 'logo': logo})

                P2pproxy.logger.debug('Exporting')
                exported = playlistgen.exportm3u(hostport)
                exported = exported.encode('utf-8')
                connection.wfile.write(exported)
            else:  # /channels/?filter=[filter]
                param_filter = self.get_param('filter')
                if not param_filter:
                    param_filter = 'all'  # default filter

                session = TorrentTvApi.auth(config.email, config.password)
                translations_list = TorrentTvApi.translations(session, param_filter, True)

                P2pproxy.logger.debug('Exporting')

                connection.send_response(200)
                connection.send_header('Access-Control-Allow-Origin', '*')
                connection.send_header('Connection', 'close')
                connection.send_header('Content-Length', str(len(translations_list)))
                connection.send_header('Content-Type', 'text/xml;charset=utf-8')
                connection.end_headers()
                connection.wfile.write(translations_list)
        elif connection.reqtype == 'xbmc.pvr':  # same as /channels request
            if len(connection.splittedpath) == 3 and connection.splittedpath[2] == 'playlist':
                session = TorrentTvApi.auth(config.email, config.password)
                translations_list = TorrentTvApi.translations(session, 'all', True)

                P2pproxy.logger.debug('Exporting')

                connection.send_response(200)
                connection.send_header('Access-Control-Allow-Origin', '*')
                connection.send_header('Connection', 'close')
                connection.send_header('Content-Length', str(len(translations_list)))
                connection.send_header('Content-Type', 'text/xml;charset=utf-8')
                connection.end_headers()
                connection.wfile.write(translations_list)
        elif connection.reqtype == 'archive':  # /archive/ branch
            if len(connection.splittedpath) == 3 and connection.splittedpath[2] == 'channels':  # /archive/channels

                session = TorrentTvApi.auth(config.email, config.password)
                archive_channels = TorrentTvApi.archive_channels(session, True)

                P2pproxy.logger.debug('Exporting')

                connection.send_response(200)
                connection.send_header('Access-Control-Allow-Origin', '*')
                connection.send_header('Connection', 'close')
                connection.send_header('Content-Length', str(len(archive_channels)))
                connection.send_header('Content-Type', 'text/xml;charset=utf-8')
                connection.end_headers()
                connection.wfile.write(archive_channels)
            if len(connection.splittedpath) == 3 and connection.splittedpath[2].split('?')[
                0] == 'play':  # /archive/play?id=[record_id]
                record_id = self.get_param('id')
                if not record_id:
                    connection.dieWithError()  # Bad request
                    return

                stream_url = None

                session = TorrentTvApi.auth(config.email, config.password)
                stream_type, stream = TorrentTvApi.archive_stream_source(session, record_id)

                if stream_type == 'torrent':
                    stream_url = re.sub('^(http.+)$',
                                        lambda match: '/torrent/' + urllib2.quote(match.group(0), '') + '/stream.mp4',
                                        stream)
                elif stream_type == 'contentid':
                    stream_url = re.sub('^([0-9a-f]{40})',
                                        lambda match: '/pid/' + urllib2.quote(match.group(0), '') + '/stream.mp4',
                                        stream)
                connection.path = stream_url
                connection.splittedpath = stream_url.split('/')
                connection.reqtype = connection.splittedpath[1].lower()
                connection.handleRequest(False)
            elif self.get_param('type') == 'm3u':  # /archive/?type=m3u&date=[param_date]&channel_id=[param_channel]
                connection.send_response(200)
                connection.send_header('Content-Type', 'application/x-mpegurl')
                connection.end_headers()

                param_date = self.get_param('date')
                if not param_date:
                    d = date.today()  # consider default date as today if not given
                else:
                    try:
                        param_date = param_date.split('-')
                        d = date(param_date[2], param_date[1], param_date[0])
                    except IndexError:
                        P2pproxy.logger.error('date param is not correct!')
                        connection.dieWithError()
                        return
                param_channel = self.get_param('channel_id')
                if param_channel == '' or not param_channel:
                    P2pproxy.logger.error('Got /archive/ request but no channel_id specified!')
                    connection.dieWithError()
                    return

                session = TorrentTvApi.auth(config.email, config.password)
                records_list = TorrentTvApi.records(session, param_channel, d.strftime('%d-%m-%Y'))
                channels_list = TorrentTvApi.archive_channels(session)

                playlistgen = PlaylistGenerator()
                P2pproxy.logger.debug('Generating archive m3u playlist')
                for record in records_list:
                    record_id = record.getAttribute('record_id')
                    name = record.getAttribute('name')
                    channel_id = record.getAttribute('channel_id')
                    channel_name = ''
                    logo = ''
                    for channel in channels_list:
                        if channel.getAttribute('channel_id') == channel_id:
                            channel_name = channel.getAttribute('name')
                            logo = channel.getAttribute('logo')

                    if channel_name != '':
                        name = '(' + channel_name + ') ' + name
                    if logo != '' and config.fullpathlogo:
                        logo = 'http://torrent-tv.ru/uploads/' + logo

                    playlistgen.addItem({'name': name, 'url': record_id, 'logo': logo})

                P2pproxy.logger.debug('Exporting')
                exported = playlistgen.exportm3u(hostport, empty_header=True, archive=True)
                exported = exported.encode('utf-8')
                connection.wfile.write(exported)
            else:  # /archive/?date=[param_date]&channel_id=[param_channel]
                param_date = self.get_param('date')
                if not param_date:
                    d = date.today()
                else:
                    try:
                        param_date = param_date.split('-')
                        d = date(param_date[2], param_date[1], param_date[0])
                    except IndexError:
                        P2pproxy.logger.error('date param is not correct!')
                        connection.dieWithError()
                        return
                param_channel = self.get_param('channel_id')
                if param_channel == '' or not param_channel:
                    P2pproxy.logger.error('Got /archive/ request but no channel_id specified!')
                    connection.dieWithError()
                    return

                session = TorrentTvApi.auth(config.email, config.password)
                records_list = TorrentTvApi.records(session, param_channel, d.strftime('%d-%m-%Y'), True)

                P2pproxy.logger.debug('Exporting')

                connection.send_response(200)
                connection.send_header('Access-Control-Allow-Origin', '*')
                connection.send_header('Connection', 'close')
                connection.send_header('Content-Length', str(len(records_list)))
                connection.send_header('Content-Type', 'text/xml;charset=utf-8')
                connection.end_headers()
                connection.wfile.write(records_list)

    def get_param(self, key):
        if key in self.params:
            return self.params[key][0]
        else:
            return None