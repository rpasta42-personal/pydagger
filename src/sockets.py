import sys
import time
import socket
import logging

LOGGER = logging.getLogger(__name__)

class TCPHandler(object):

   def __init__(self, sock, address, handler):
      self.sock = sock
      self.sock.setblocking(0)
      self.address = address
      self.handler = handler
      self.reader = TCPReader(self.sock)
      self.writer = TCPWriter(self.sock)
      self.connected = True
      self.on_connected()

   def __del__(self):
      if self.connected:
         self.disconnect()

   def disconnect(self):
      if self.connected:
         self.connected = False
         self.sock.close()

   def update(self):
      packet = self.reader.update()
      if packet:
         self.on_data(packet)
      self.writer.update()

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

class TCPServer(object):

   def __init__(self, ip, port, handler, listen=-1):
      self.address = (ip, port)
      self.handler = handler
      self.handlers = list()
      self.listen = listen
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.started = False

   def __del__(self):
      if self.started:
         for client in self.handlers:
            client.disconnect()

         self.stop()

   def start(self):
      try:
         self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
         self.sock.bind(self.address)
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
            handler = TCPHandler(sock, address, self.handler)
            self.handlers.append(handler)

            if self.listen != -1:
               listen_count = len(self.handlers)
         except socket.error as e:
            listen_count /= 2
            if listen_count == 0:
               listen_count = 1

         if handler:
            handler.update()

         if len(self.handlers) > 0:
            handler = self.handlers[i%len(self.handlers)]
            i = 0 if i > len(self.handlers) else i+1

         yield len(self.handlers)

   def update_sync(self):
      for busy in self.update():
         if busy < 100:
            time.sleep(0.01)

class TCPClient(object):

   def __init__(self, ip, port, handler=None):
      self.address = (ip, port)
      self.handler = handler
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.reader = TCPReader(self.sock)
      self.writer = TCPWriter(self.sock)
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
            LOGGER.debug(ex)

   def on_connected(self):
      if self.handler:
         try:
            self.handler('on_connected', self)
         except Exception as ex:
            LOGGER.debug(ex)

   def update(self):
      packet = self.reader.update()
      if packet:
         self.on_data(packet)
      self.writer.update()

   def update_sync(self):
      while self.connected:
         self.update()
         time.sleep(0.01)

   def send(self, data):
      self.writer.send(data)

class TCPWriter(object):

   def __init__(self, sock):
      self.sock = sock
      self.send_buffer = bytearray()

   def update(self):
      try:
         sent = self.sock.send(self.send_buffer)
         if sent > 0:
            del self.send_buffer[:sent]
      except socket.error as e:
         LOGGER.debug(e)

   def send(self, data):
      assert isinstance(data, bytes), "Data must be bytes"
      self.send_buffer.extend(data)

class TCPReader(object):

   def __init__(self, sock):
      self.sock = sock
      self.buffer_size = 1024

   def update(self):
      try:
         packet = self.sock.recv(self.buffer_size)
         if packet:
            return packet
      except BlockingIOError as bio:
         pass
      except socket.error as e:
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

   ip, port = ('0.0.0.0', 7890)

   if sys.argv[1] == 'server':
      LOGGER.debug("STARTING SERVER")
      srv = TCPServer(ip, port, server_handle)
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
         client = TCPClient(ip, port, client_handle)
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


