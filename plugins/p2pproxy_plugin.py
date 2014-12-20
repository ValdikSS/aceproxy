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
__author__ = 'miltador'

import logging
import re
import urllib2
import urlparse
from datetime import date
from xml.dom.minidom import parseString

from modules.PluginInterface import AceProxyPlugin
from modules.PlaylistGenerator import PlaylistGenerator
import config.p2pproxy


class P2pproxy(AceProxyPlugin):
    handlers = ('channels', 'archive', 'xbmc.pvr')

    logger = logging.getLogger('plugin_p2pproxy')

    email = config.p2pproxy.email
    password = config.p2pproxy.password

    session = None

    xml = None
    translationslist = None

    recordslist = None
    channelslist = None

    categories = dict()

    def __init__(self, AceConfig, AceStuff):
        super(P2pproxy, self).__init__(AceConfig, AceStuff)

    def downloadPlaylist(self, trans_type, raw_only=False):
        # First of all, authorization and getting session
        if P2pproxy.session is None:  # we need to auth only once
            if not self.auth():
                return False

        # Now we get translations and categories lists
        if not self.getTranslations(trans_type, raw_only):
            return False
        return True

    def handle(self, connection):
        P2pproxy.logger.debug('Handling request')
        if not self.auth():
            connection.dieWithError()
            return

        hostport = connection.headers['Host']

        query = urlparse.urlparse(connection.path).query
        self.params = urlparse.parse_qs(query)

        if connection.reqtype == 'channels':
            if len(connection.splittedpath) == 3 and connection.splittedpath[2].split('?')[0] == 'play':
                record_id = self.getparam('id')
                if record_id is None:
                    connection.dieWithError()  # Bad request
                    return

                stream_url = None
                stream_type, stream = self.getSource(record_id)
                if stream_type == 'torrent':
                    stream_url = re.sub('^(http.+)$', lambda match: '/torrent/' + \
                                                                    urllib2.quote(match.group(0), '') + '/stream.mp4',
                                        stream)
                elif stream_type == 'contentid':
                    stream_url = re.sub('^([0-9a-f]{40})', lambda match: '/pid/' + \
                                                                         urllib2.quote(match.group(0), '') + '/stream.mp4',
                                        stream)
                connection.path = stream_url
                connection.splittedpath = stream_url.split('/')
                connection.reqtype = connection.splittedpath[1].lower()
                connection.handleRequest(False)
            elif self.getparam('type') == 'm3u':
                connection.send_response(200)
                connection.send_header('Content-Type', 'application/x-mpegurl')
                connection.end_headers()

                param_group = self.getparam('group')
                param_filter = self.getparam('filter')
                if param_filter is not None:
                    self.downloadPlaylist(param_filter)
                else:
                    self.downloadPlaylist('all')
                playlistgen = PlaylistGenerator()
                P2pproxy.logger.debug('Generating requested m3u playlist')
                for channel in P2pproxy.translationslist:
                    groupid = channel.getAttribute('group')
                    if param_group is not None and param_group != 'all' and param_group != groupid:
                        continue
                    name = channel.getAttribute('name')
                    group = P2pproxy.categories[groupid]

                    cid = channel.getAttribute('id')

                    logo = channel.getAttribute('logo')
                    if config.p2pproxy.fullpathlogo:
                        logo = 'http://torrent-tv.ru/uploads/' + logo
                    playlistgen.addItem({'name': name, 'url': cid, 'group': group, 'logo': logo})

                P2pproxy.logger.debug('Exporting')
                exported = playlistgen.exportm3u(hostport)
                exported = exported.encode('utf-8')
                connection.wfile.write(exported)
            else:
                param_filter = self.getparam('filter')
                if param_filter is not None:
                    self.downloadPlaylist(param_filter, True)
                else:
                    self.downloadPlaylist('all', True)
                P2pproxy.logger.debug('Exporting')

                connection.send_response(200)
                connection.send_header('Access-Control-Allow-Origin', '*')
                connection.send_header('Connection', 'close')
                connection.send_header('Content-Length', str(len(P2pproxy.xml)))
                connection.send_header('Content-Type', 'text/xml;charset=utf-8')
                connection.end_headers()
                connection.wfile.write(P2pproxy.xml)
        elif connection.reqtype == 'xbmc.pvr':  # same as /channels request
            if len(connection.splittedpath) == 3 and connection.splittedpath[2] == 'playlist':
                self.downloadPlaylist('all', True)
                P2pproxy.logger.debug('Exporting')

                connection.send_response(200)
                connection.send_header('Access-Control-Allow-Origin', '*')
                connection.send_header('Connection', 'close')
                connection.send_header('Content-Length', str(len(P2pproxy.xml)))
                connection.send_header('Content-Type', 'text/xml;charset=utf-8')
                connection.end_headers()
                connection.wfile.write(P2pproxy.xml)
        elif connection.reqtype == 'archive':
            if len(connection.splittedpath) == 3 and connection.splittedpath[2] == 'channels':
                self.getChannels()
                P2pproxy.logger.debug('Exporting')

                connection.send_response(200)
                connection.send_header('Access-Control-Allow-Origin', '*')
                connection.send_header('Connection', 'close')
                connection.send_header('Content-Length', str(len(P2pproxy.xml)))
                connection.send_header('Content-Type', 'text/xml;charset=utf-8')
                connection.end_headers()
                connection.wfile.write(P2pproxy.xml)
            if len(connection.splittedpath) == 3 and connection.splittedpath[2].split('?')[0] == 'play':
                record_id = self.getparam('id')
                if record_id is None:
                    connection.dieWithError()  # Bad request
                    return

                stream_url = None
                stream_type, stream = self.getStreamSource(record_id)
                if stream_type == 'torrent':
                    stream_url = re.sub('^(http.+)$', lambda match: '/torrent/' + \
                                                                    urllib2.quote(match.group(0), '') + '/stream.mp4',
                                        stream)
                elif stream_type == 'contentid':
                    stream_url = re.sub('^([0-9a-f]{40})', lambda match: '/pid/' + \
                                                                         urllib2.quote(match.group(0), '') + '/stream.mp4',
                                        stream)
                connection.path = stream_url
                connection.splittedpath = stream_url.split('/')
                connection.reqtype = connection.splittedpath[1].lower()
                connection.handleRequest(False)
            elif self.getparam('type') == 'm3u':
                connection.send_response(200)
                connection.send_header('Content-Type', 'application/x-mpegurl')
                connection.end_headers()

                param_date = self.getparam('date')
                if param_date is None:
                    d = date.today()
                else:
                    try:
                        param_date = param_date.split('-')
                        d = date(param_date[2], param_date[1], param_date[0])
                    except IndexError:
                        P2pproxy.logger.error('date param is not correct!')
                        connection.dieWithError()
                        return
                param_channel = self.getparam('channel_id')
                if param_channel is None:
                    param_channel = 'all'

                self.getRecords(param_channel, d.strftime('%d-%m-%Y'))
                self.getChannels()

                playlistgen = PlaylistGenerator()
                P2pproxy.logger.debug('Generating archive m3u playlist')
                for record in P2pproxy.recordslist:
                    record_id = record.getAttribute('record_id')
                    name = record.getAttribute('name')
                    channel_id = record.getAttribute('channel_id')
                    channel_name = ''
                    logo = ''
                    for channel in P2pproxy.channelslist:
                        if channel.getAttribute('channel_id') == channel_id:
                            channel_name = channel.getAttribute('name')
                            logo = channel.getAttribute('logo')

                    if channel_name != '':
                        name = '(' + channel_name + ') ' + name
                    if logo != '' and config.p2pproxy.fullpathlogo:
                        logo = 'http://torrent-tv.ru/uploads/' + logo

                    playlistgen.addItem({'name': name, 'url': record_id, 'logo': logo})

                P2pproxy.logger.debug('Exporting')
                exported = playlistgen.exportm3u(hostport, empty_header=True, archive=True)
                exported = exported.encode('utf-8')
                connection.wfile.write(exported)
            else:
                param_date = self.getparam('date')
                if param_date is None:
                    d = date.today()
                else:
                    try:
                        param_date = param_date.split('-')
                        d = date(param_date[2], param_date[1], param_date[0])
                    except IndexError:
                        P2pproxy.logger.error('date param is not correct!')
                        connection.dieWithError()
                        return
                param_channel = self.getparam('channel_id')
                if param_channel is None:
                    param_channel = 'all'
                self.getRecords(param_channel, d.strftime('%d-%m-%Y'), True)
                P2pproxy.logger.debug('Exporting')

                connection.send_response(200)
                connection.send_header('Access-Control-Allow-Origin', '*')
                connection.send_header('Connection', 'close')
                connection.send_header('Content-Length', str(len(P2pproxy.xml)))
                connection.send_header('Content-Type', 'text/xml;charset=utf-8')
                connection.end_headers()
                connection.wfile.write(P2pproxy.xml)

    def getparam(self, key):
        if key in self.params:
            return self.params[key][0]
        else:
            return None

# ============================================ [ API ] ============================================

    '''
    Every API request returns if it is successfull and if no, gives a reason
    '''

    def checkRequestSuccess(self, res):
        success = res.getElementsByTagName('success')[0].childNodes[0].data
        if success == 0 or success is None:
            error = res.getElementsByTagName('error')[0].childNodes[0].data
            P2pproxy.logger.error('Failed to perform the torrent-tv API request, reason: ' +
                                  error)
            if error == 'incorrect':  # trying to fix
                P2pproxy.logger.error('Incorrect login data, check config file!')
                return False
        return True

    '''
    Refreshes current session
    '''

    def auth(self):
        try:
            P2pproxy.logger.debug('Trying to access torrent-tv API')
            xmlresult = urllib2.urlopen(
                'http://api.torrent-tv.ru/v2_auth.php?username=' + P2pproxy.email + '&password=' + P2pproxy.password +
                '&application=tsproxy&typeresult=xml', timeout=10).read()
        except:
            P2pproxy.logger.error("Can't auth! Maybe torrent-tv is down")
            return False

        res = parseString(xmlresult).documentElement
        if self.checkRequestSuccess(res):
            P2pproxy.session = res.getElementsByTagName('session')[0].childNodes[0].data
            return True
        else:
            return False

    '''
    Gets list of available translations
    '''

    def getTranslations(self, trans_type, raw_only):
        try:
            P2pproxy.logger.debug('Trying to get the playlist from torrent-tv')
            P2pproxy.xml = urllib2.urlopen(
                'http://api.torrent-tv.ru/v2_alltranslation.php?session=' + P2pproxy.session +
                '&type=' + trans_type + '&typeresult=xml', timeout=10).read()
        except:
            P2pproxy.logger.error("Can't get translations! Maybe torrent-tv is down")
            return False

        res = parseString(P2pproxy.xml).documentElement
        if not raw_only:
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
        return True

    '''
    Gets list of available records of channel_id by date
    '''

    def getRecords(self, channel_id, date, raw_only=False):
        try:
            P2pproxy.logger.debug('Trying to get the records list from torrent-tv')
            P2pproxy.xml = urllib2.urlopen(
                'http://api.torrent-tv.ru/v2_arc_getrecords.php?session=' + P2pproxy.session +
                '&channel_id=' + channel_id + '&date=' + date + '&typeresult=xml', timeout=10).read()
        except:
            P2pproxy.logger.error("Can't get records! Maybe torrent-tv is down")
            return False

        res = parseString(P2pproxy.xml).documentElement
        if not raw_only:
            if self.checkRequestSuccess(res):
                P2pproxy.recordslist = res.getElementsByTagName('channel')
                return True
            else:
                return False
        return True

    '''
    Gets the channels list for archive
    '''

    def getChannels(self):
        try:
            P2pproxy.logger.debug('Trying to get the channels list from torrent-tv')
            P2pproxy.xml = urllib2.urlopen(
                'http://api.torrent-tv.ru/v2_arc_getchannels.php?session=' + P2pproxy.session +
                '&typeresult=xml', timeout=10).read()
        except:
            P2pproxy.logger.error("Can't get channels list! Maybe torrent-tv is down")
            return False

        res = parseString(P2pproxy.xml).documentElement
        if self.checkRequestSuccess(res):
            P2pproxy.channelslist = res.getElementsByTagName('channel')
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
        P2pproxy.logger.debug('Getting source for channel id: ' + channelId)
        try:
            xmlresult = urllib2.urlopen(
                'http://api.torrent-tv.ru/v2_get_stream.php?session=' + P2pproxy.session +
                '&channel_id=' + channelId + '&typeresult=xml', timeout=10).read()
        except:
            P2pproxy.logger.error("Can't get channel source! Maybe torrent-tv is down")
            return None, None
        res = parseString(xmlresult).documentElement
        if self.checkRequestSuccess(res):
            return res.getElementsByTagName('type')[0].childNodes[0].data.encode('utf-8'), \
                   res.getElementsByTagName('source')[0].childNodes[0].data.encode('utf-8')
        else:
            return None, None

    '''
    Gets stream source for archive record
    '''
    def getStreamSource(self, record_id):
        if P2pproxy.session is None:
            if not self.auth():
                return None, None
        P2pproxy.logger.debug('Getting stream for record id: ' + record_id)
        try:
            xmlresult = urllib2.urlopen(
                'http://api.torrent-tv.ru/v2_arc_getstream.php?session=' + P2pproxy.session +
                '&record_id=' + record_id + '&typeresult=xml', timeout=10).read()
        except:
            P2pproxy.logger.error("Can't get stream source! Maybe torrent-tv is down")
            return None, None
        res = parseString(xmlresult).documentElement
        if self.checkRequestSuccess(res):
            return res.getElementsByTagName('type')[0].childNodes[0].data.encode('utf-8'), \
                   res.getElementsByTagName('source')[0].childNodes[0].data.encode('utf-8')
        else:
            return None, None
# =================================================================================================