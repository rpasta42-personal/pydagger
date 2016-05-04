import os
import sys
import time
import socket
import logging
import traceback
from struct import unpack

LOGGER = logging.getLogger(__name__)

class SocketHandler(object):

    def __init__(self, sock, address, handler):
        self.sock = sock
        self.sock.setblocking(0)
        self.address = address
        self.handler = handler
        self.reader = SocketReader(self.sock)
        self.writer = SocketWriter(self.sock)
        self.connected = True
        self.on_connected()
        try:
            ucred = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
            self._pid, self._uid, self._gid = unpack('III', ucred)
        except Exception as ex:
            LOGGER.exception(ex)
            self._pid = False
            self._uid = False
            self._gid = False

    def __del__(self):
        if self.connected:
            self.disconnect()

    def get_uid(self):
        return self._uid

    def get_gid(self):
        return self._gid

    def get_pid(self):
        return self._pid

    def disconnect(self):
        if self.connected:
            self.connected = False
            self.sock.close()

    def update(self):
        try:
            packet = self.reader.update()
            if packet:
                self.on_data(packet)
            self.writer.update()
            return True
        except OSError as ose:
            self.connected = False
            return False
        except BrokenPipeError as bpe:
            self.connected = False
            return False

    def on_data(self, data):
        if self.handler:
            try:
                self.handler('on_data', self, data)
            except Exception as ex:
                LOGGER.exception(ex)

    def on_connected(self):
        if self.handler:
            try:
                self.handler('new_client', self)
            except Exception as ex:
                LOGGER.exception(ex)

class SocketServer(object):

    @classmethod
    def new_tcp_server(cls, ip, port, handler, listen=-1):
        return cls((ip, port), handler, listen, socket_type=socket.AF_INET)

    @classmethod
    def new_unix_server(cls, address, handler, listen=-1, permissions=None):
        return cls(address, handler, listen, socket_type=socket.AF_UNIX, permissions=permissions)

    def __init__(self, address, handler, listen=-1, socket_type=socket.AF_INET, permissions=None):
        self.address = address
        self.handler = handler
        self.handlers = list()
        self.permissions = permissions
        self.listen = listen
        if socket_type == socket.AF_UNIX:
            try:
                os.unlink(self.address)
            except OSError:
                if os.path.exists(self.address):
                    raise

        self.started = False
        self.sock = socket.socket(socket_type, socket.SOCK_STREAM)

    def __del__(self):
        if self.started:
            self.stop()

    def start(self):
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(self.address)
            if self.permissions:
                if isinstance(self.permissions, int):
                    os.chmod(self.address, self.permissions)
                elif isinstance(self.permissions, list) or isinstance(self.permissions, tuple):
                    os.chmod(self.address, self.permissions[1])
                    os.chown(self.address, self.permissions[0][0], self.permissions[0][1])
            self.sock.setblocking(0)
            self.started = True
            return True
        except OSError as ose:
            LOGGER.error(ose)
            raise ose
        except socket.error as e:
            LOGGER.error(e)
            raise e

    def stop(self):
        self.started = False
        for client in self.handlers:
            client.disconnect()
        self.sock.close()

    def update(self):
        handler = None
        i = 0
        listen_count = 1
        while 1:
            try:
                if self.listen != -1:
                    listen_count = self.listen

                self.sock.listen(listen_count)
                sock, address = self.sock.accept()
                handler = SocketHandler(sock, address, self.handler)
                self.handlers.append(handler)

                if self.listen != -1:
                    listen_count = len(self.handlers)
            except socket.error as e:
                listen_count /= 2
                if listen_count == 0:
                    listen_count = 1

            if handler:
                if not handler.update():
                    del self.handlers[self.handlers.index(handler)]
                    handler = None

            if len(self.handlers) > 0:
                handler = self.handlers[i%len(self.handlers)]
                i = 0 if i > len(self.handlers) else i+1

            yield len(self.handlers)

    def update_sync(self):
        for busy in self.update():
            if busy < 100:
                time.sleep(0.01)

class SocketClient(object):

    @classmethod
    def new_tcp_client(cls, ip, port, handler):
        return cls((ip, port), handler, socket_type=socket.AF_INET)

    @classmethod
    def new_unix_client(cls, address, handler):
        return cls(address, handler, socket_type=socket.AF_UNIX)

    def __init__(self, address, handler=None, socket_type=socket.AF_INET):
        self.address = address
        self.handler = handler
        self.sock = socket.socket(socket_type, socket.SOCK_STREAM)
        self.reader = SocketReader(self.sock)
        self.writer = SocketWriter(self.sock)
        self.connected = False

    def __del__(self):
        if self.connected:
            self.disconnect()

    def connect(self):
        self.sock.connect(self.address)
        self.sock.setblocking(0)
        self.connected = True
        self.on_connected()
        return True

    def disconnect(self):
        self.connected = False
        self.sock.close()

    def on_data(self, data):
        if self.handler:
            try:
                self.handler('on_data', self, data)
            except Exception as ex:
                LOGGER.info(data)
                LOGGER.debug(ex)
                LOGGER.debug(traceback.format_exc())

    def on_connected(self):
        if self.handler:
            try:
                self.handler('on_connected', self)
            except Exception as ex:
                LOGGER.debug(ex)

    def update(self):
        try:
            packet = self.reader.update()
            if packet:
                self.on_data(packet)
            self.writer.update()
            return True
        except BrokenPipeError as bpe:
            self.connected = False
            return False

    def update_sync(self):
        while self.connected:
            if not self.update():
                return
            time.sleep(0.01)

    def send(self, data):
        self.writer.send(data)

class SocketWriter(object):

    def __init__(self, sock):
        self.sock = sock
        self.send_buffer = bytearray()

    def update(self):
        try:
            sent = self.sock.send(self.send_buffer)
            if sent > 0:
                del self.send_buffer[:sent]
        except BrokenPipeError as bpe:
            raise bpe
        except OSError as ose:
            raise ose
        except socket.error as e:
            LOGGER.debug(e)

    def send(self, data):
        assert isinstance(data, bytes), "Data must be bytes"
        self.send_buffer.extend(data)

class SocketReader(object):

    def __init__(self, sock):
        self.sock = sock
        self.buffer_size = 1024

    def update(self):
        try:
            packet = self.sock.recv(self.buffer_size)
            if len(packet) == 0:
                raise BrokenPipeError("Disconnected")
            if packet:
                return packet
        except BlockingIOError as bio:
            pass
        except BrokenPipeError as bpe:
            raise bpe
        except OSError as ose:
            raise ose
        except socket.error as e:
            traceback.print_exc()
            LOGGER.exception(e)

        return False


if __name__ == '__main__':


    logging.basicConfig(level=logging.DEBUG)
    LOGGER.setLevel(logging.DEBUG)

    def server_handle(e, client, data=None):
        LOGGER.debug("[%s] [%s] %s", client.address, e, data if data else "")
        if e == 'new_client':
            client.writer.send(bytes('HI CLIENT %s' % str(client.address), 'ascii'))

    def client_handle(e, client, data=None):
        LOGGER.debug("[%s] %s", e, data if data else "")
        if e == 'on_connected':
            client.writer.send(b'HI SERVER!')

    #address = ('127.0.0.1', 7890)
    address = '/tmp/test.pid'

    if sys.argv[1] == 'server':
        LOGGER.debug("STARTING SERVER")
        srv = SocketServer.new_unix_server(address, server_handle)
        try:
            srv.start()
            srv.update_sync()
        finally:
            srv.stop()

    elif sys.argv[1] == 'client':
        total = 1
        if len(sys.argv) > 2:
            total = int(sys.argv[2])

        LOGGER.debug("STARTING CLIENT")
        clients = []
        for i in range(0, total):
            client = SocketClient.new_unix_client(address, client_handle)
            clients.append(client)
            client.connect()

        counter=0
        try:
            while 1:
                for client in clients:
                    client.update()
                    counter += 1
                    client.writer.send(bytes(str(counter), 'ascii'))
                time.sleep(.1)
        finally:
            client.disconnect()
