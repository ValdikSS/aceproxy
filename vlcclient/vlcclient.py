'''
Minimal VLC VLM client for AceProxy. Client class.
'''

import gevent
import gevent.event
import gevent.coros
import telnetlib
import logging
from vlcmessages import *


class VlcException(Exception):

    '''
    Exception from VlcClient
    '''
    pass


class VlcClient(object):

    '''
    VLC Client class
    '''

    def __init__(
        self, host='127.0.0.1', port=4212, password='admin', connect_timeout=5,
            result_timeout=5, out_port=8081):
        # Receive buffer
        self._recvbuffer = None
        # Output port
        self._out_port = out_port
        # VLC socket
        self._socket = None
        # Result timeout
        self._resulttimeout = result_timeout
        # Shutting down flag
        self._shuttingDown = gevent.event.Event()
        # Authentication done event
        self._auth = gevent.event.AsyncResult()
        # Request lock
        self._resultlock = gevent.coros.RLock()
        # Request result
        self._result = gevent.event.AsyncResult()
        # VLC version string
        self._vlcver = None
        # Saving password
        self._password = password

        # Logger
        logger = logging.getLogger('VlcClient_init')

        # Making connection
        try:
            self._socket = telnetlib.Telnet(host, port, connect_timeout)
            logger.debug("Successfully connected with VLC socket!")
        except Exception as e:
            raise VlcException(
                "Socket creation error! VLC is not running? ERROR: " + repr(e))

        # Spawning recvData greenlet
        gevent.spawn(self._recvData)
        gevent.sleep()

        # Waiting for authentication event
        try:
            if self._auth.get(timeout=self._resulttimeout) == False:
                errmsg = "Authentication error"
                logger.error(errmsg)
                raise VlcException(errmsg)
        except gevent.Timeout:
            errmsg = "Authentication timeout"
            logger.error(errmsg)
            raise VlcException(errmsg)

    def __del__(self):
        # Destructor just calls destroy() method
        self.destroy()

    def destroy(self):
        # Logger
        logger = logging.getLogger("VlcClient_destroy")

        if self._shuttingDown.isSet():
            # Already in the middle of destroying
            return

        # If socket is still alive (connected)
        if self._socket:
            try:
                logger.debug("Destroying VlcClient...")
                self._write(VlcMessage.request.SHUTDOWN)
                # Set shuttingDown flag for recvData
                self._shuttingDown.set()
            except:
                # Ignore exceptions on destroy
                pass

    def _write(self, message):
        # Return if in the middle of destroying
        if self._shuttingDown.isSet():
            return

        try:
            # Write message
            self._socket.write(message + "\r\n")
        except EOFError as e:
            raise VlcException("Vlc Write error! ERROR: " + repr(e))

    def _broadcast(self, brtype, stream_name, input=None, muxer='ts', pre_access=''):
        # Start/stop broadcast with VLC
        # Logger
        if brtype == True:
            broadcast = 'startBroadcast'
        else:
            broadcast = 'stopBroadcast'

        logger = logging.getLogger("VlcClient_" + broadcast)
        # Clear AsyncResult
        self._result = gevent.event.AsyncResult()
        # Get lock
        self._resultlock.acquire()
        # Write message to VLC socket
        if brtype == True:
            self._write(VlcMessage.request.startBroadcast(
                stream_name, input, self._out_port, muxer, pre_access))
        else:
            self._write(VlcMessage.request.stopBroadcast(stream_name))

        try:
            gevent.sleep()
            result = self._result.get(timeout=self._resulttimeout)
            if result == False:
                logger.error(broadcast + " error")
                raise VlcException(broadcast + " error")
        except gevent.Timeout:
            logger.error(broadcast + " result timeout")
            raise VlcException(broadcast + " result timeout")
        finally:
            self._resultlock.release()

        if brtype == True:
            logger.debug("Broadcast started")
        else:
            logger.debug("Broadcast stopped")

    def startBroadcast(self, stream_name, input, muxer='ts', pre_access=''):
        return self._broadcast(True, stream_name, input, muxer, pre_access)

    def stopBroadcast(self, stream_name):
        return self._broadcast(False, stream_name)

    def _recvData(self):
        # Logger
        logger = logging.getLogger("VlcClient_recvData")

        while True:
            gevent.sleep()
            try:
                self._recvbuffer = self._socket.read_until("\n")
                # Stripping "> " from VLC
                self._recvbuffer = self._recvbuffer.lstrip("> ")
            except:
                # If something happened during read, abandon reader
                if not self._shuttingDown.isSet():
                    logger.error("Exception at socket read")
                    self._shuttingDown.set()
                return

            # Parsing everything only if the string is not empty
            if self._recvbuffer:
                if not self._vlcver:
                    # First line (VLC version)
                    self._vlcver = self._recvbuffer.strip()
                    # Send password here since PASSWORD doesn't have \n
                    self._write(self._password)

                elif self._recvbuffer.startswith(VlcMessage.response.SHUTDOWN):
                    # Exit from this loop
                    logger.debug("Got SHUTDOWN from VLC")
                    return

                elif self._recvbuffer.startswith(VlcMessage.response.WRONGPASS):
                    # Wrong password
                    logger.error("Wrong VLC password!")
                    self._auth.set(False)
                    return

                elif self._recvbuffer.startswith(VlcMessage.response.AUTHOK):
                    # Authentication OK
                    logger.info("Authentication successful")
                    self._auth.set(True)

                elif VlcMessage.response.BROADCASTEXISTS in self._recvbuffer:
                    # Broadcast already exists
                    logger.error("Broadcast already exists!")
                    self._result.set(False)

                elif VlcMessage.response.STOPERR in self._recvbuffer:
                    # Media unknown (stopping non-existent stream)
                    logger.error("Broadcast does not exist!")
                    self._result.set(False)

                # Do not move this before error handlers!
                elif self._recvbuffer.startswith(VlcMessage.response.STARTOK):
                    # Broadcast started
                    logger.debug("Broadcast started")
                    self._result.set(True)

                elif self._recvbuffer.startswith(VlcMessage.response.STOPOK):
                    # Broadcast stopped
                    logger.debug("Broadcast stopped")
                    self._result.set(True)
