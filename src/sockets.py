import socket

class TCPHandler(object):

   def __init__(self, sock, address, handler):
      self.sock = sock
      self.sock.setblocking(0)
      self.address = address
      self.handler = handler
      self.reader = TCPReader(self.socket)
      self.reader_update = self.reader.update()
      self.writer = TCPWriter(self.socket)
      self.writer_udpate = self.writer.update()

   def update(self):
      packet = next(self.reader_update)
      if packet:
         self.on_data(data)

      next(self.writer_update)

   def on_data(self, data):
      if self.handler:
         self.handler(self, data)

class TCPServer(object):

   def __init__(self, ip, port, handler):
      self.address = (ip, port)
      self.handler = handler
      self.handlers = list()
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

   def start(self):
      try:
         self.sock.bind(self.address)
         self.sock.setblocking(0)
         self.sock.listen(1)
         return True
      except socket.error as e:
         raise e

   def update(self):
      while 1:
         try:
            sock, address = self.sock.accept()
            handler = TCPHandler(sock, address, self.handler)
            self.handlers.append(handler)
            handler.writer.send("WELCOME CLIENT")
            print("[SERVER] NEW CLIENT CONNECTED")
         except socket.error as e:
            pass

         yield

         for handler in self.handlers:
            next(handler.update())
            yield

class TCPClient(object):

   def __init__(self, ip, port, handler=None):
      self.address = (ip, port)
      self.handler = handler
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.reader = TCPReader(self.sock)
      self.reader_update = self.reader.update()
      self.writer = TCPWriter(self.sock)
      self.writer_update = self.writer.update()

   def connect(self):
      self.sock.connect(self.address)
      self.sock.setblocking(0)

   def on_data(self, data):
      if self.handler:
         handler(self, data)

   def update(self):
      packet = next(self.reader_update)
      if packet:
         self.on_data(packet)

      next(self.writer_update)
      yield

   def send(self, data):
      self.writer.send(data)

class TCPWriter(object):

   def __init__(self, sock):
      self.sock = sock
      self.send_buffer = bytearray()

   def update(self):
      while 1:
         try:
            sent = self.sock.send(self.send_buffer)
            if sent > 0:
               print("SENT: %s bytes" % sent)
               del self.send_buffer[:sent]
         except socket.error as e:
            print(e)
            pass

         yield


   def send(self, data):
      self.send_buffer.extend(bytes(data))
      print(self.send_buffer)


class TCPReader(object):

   def __init__(self, sock):
      self.sock = sock

   def update(self):
      while 1:
         try:
            packet = self.sock.recv(n)
            if packet:
               yield packet
         except socket.error as e:
            yield False


if __name__ == '__main__':

   def server_handle(client, data):
      print("%s: %s" % (client.ip, data))
      client.send('HI FROM SERVER! to %s: %s' % (client.ip, data))

   def client_handle(client, data):
      print("SERVER: %s" % data)

   ip, port = ('0.0.0.0', 7890)
   srv = TCPServer(ip, port, server_handle)
   srv.start()

   init=False
   clients = []

   count = 0
   while 1:
      if not init:
         init = True
         for i in range(0, 10):
            client=TCPClient(ip, port, client_handle)
            clients.append(client)
            client.connect()
            srv.update()

         print("TOTAL CLIENTS SPAWNED: %s" % len(clients))

      srv.update()
      i=0
      for client in clients:
         client.update()
         client.send("HI! %s" % count)
         i+= 1
         count += 1


