# coding=utf-8
"""
Torrent-TV API communication class
Forms requests to API, checks result for errors and returns in desired form (lists or raw data)
"""
__author__ = 'miltador'

import urllib2
import xml.dom.minidom as dom


class TorrentTvApiException(Exception):
    """
    Exception from Torrent-TV API
    """
    pass


class TorrentTvApi(object):
    CATEGORIES = {
        1: 'Детские',
        2: 'Музыка',
        3: 'Фильмы',
        4: 'Спорт',
        5: 'Общие',
        6: 'Познавательные',
        7: 'Новостные',
        8: 'Развлекательные',
        9: 'Для взрослых',
        10: 'Мужские',
        11: 'Региональные',
        12: 'Религиозные'
    }

    @staticmethod
    def auth(email, password, raw=False):
        """
        User authentication
        Returns user session that can be used for API requests

        :param email: user email string
        :param password: user password string
        :param raw: if True returns unprocessed data
        :return: unique session string
        """

        xmlresult = TorrentTvApi._result(
            'v2_auth.php?username=' + email + '&password=' + password + '&application=tsproxy')
        if raw:
            return xmlresult
        res = TorrentTvApi._check(xmlresult)
        session = res.getElementsByTagName('session')[0].firstChild.data
        return session

    @staticmethod
    def translations(session, translation_type, raw=False):
        """
        Gets list of translations
        Translations are basically TV channels

        :param session: valid user session required
        :param translation_type: playlist type, valid values: all|channel|moderation|translation|favourite
        :param raw: if True returns unprocessed data
        :return: translations list
        """
        xmlresult = TorrentTvApi._result(
            'v2_alltranslation.php?session=' + session + '&type=' + translation_type)
        if raw:
            return xmlresult
        res = TorrentTvApi._check(xmlresult)
        translationslist = res.getElementsByTagName('channel')
        return translationslist

    @staticmethod
    def records(session, channel_id, date, raw=False):
        """
        Gets list of available record for given channel and date

        :param session: valid user session required
        :param channel_id: id of channel in channel list
        :param date: format %d-%m-%Y
        :param raw: if True returns unprocessed data
        :return: records list
        """
        xmlresult = TorrentTvApi._result(
            'v2_arc_getrecords.php?session=' + session + '&channel_id=' + channel_id + '&date=' + date)
        if raw:
            return xmlresult
        res = TorrentTvApi._check(xmlresult)
        recordslist = res.getElementsByTagName('channel')
        return recordslist

    @staticmethod
    def archive_channels(session, raw=False):
        """
        Gets the channels list for archive

        :param session: valid user session required
        :param raw: if True returns unprocessed data
        :return: archive channels list
        """
        xmlresult = TorrentTvApi._result(
            'v2_arc_getchannels.php?session=' + session)
        if raw:
            return xmlresult
        res = TorrentTvApi._check(xmlresult)
        archive_channelslist = res.getElementsByTagName('channel')
        return archive_channelslist

    @staticmethod
    def stream_source(session, channel_id):
        """
        Gets the source for Ace Stream by channel id

        :param session: valid user session required
        :param channel_id: id of channel in translations list (see translations() method)
        :return: type of stream and source
        """
        xmlresult = TorrentTvApi._result(
            'v2_get_stream.php?session=' + session + '&channel_id=' + channel_id)
        res = TorrentTvApi._check(xmlresult)
        stream_type = res.getElementsByTagName('type')[0].firstChild.data
        source = res.getElementsByTagName('source')[0].firstChild.data
        return stream_type.encode('utf-8'), source.encode('utf-8')

    @staticmethod
    def archive_stream_source(session, record_id):
        """
        Gets stream source for archive record

        :param session: valid user session required
        :param record_id: id of record in records list (see records() method)
        :return: type of stream and source
        """
        xmlresult = TorrentTvApi._result(
            'v2_arc_getstream.php?session=' + session + '&record_id=' + record_id)
        res = TorrentTvApi._check(xmlresult)
        stream_type = res.getElementsByTagName('type')[0].firstChild.data
        source = res.getElementsByTagName('source')[0].firstChild.data
        return stream_type.encode('utf-8'), source.encode('utf-8')

    @staticmethod
    def _check(xmlresult):
        """
        Validates received API answer
        Raises an exception if error detected

        :param xmlresult: API answer to check
        :return: minidom-parsed xmlresult
        :raise: TorrentTvApiException
        """
        res = dom.parseString(xmlresult).documentElement
        success = res.getElementsByTagName('success')[0].firstChild.data
        if success == '0' or not success:
            error = res.getElementsByTagName('error')[0].firstChild.data
            raise TorrentTvApiException('API returned error: ' + error)
        return res

    @staticmethod
    def _result(request):
        """
        Sends request to API and returns the result in form of string

        :param request: API command string
        :return: result of request to API
        :raise: TorrentTvApiException
        """
        try:
            result = urllib2.urlopen('http://api.torrent-tv.ru/' + request + '&typeresult=xml', timeout=10).read()
            return result
        except urllib2.URLError as e:
            raise TorrentTvApiException('Error happened while trying to access API: ' + repr(e))