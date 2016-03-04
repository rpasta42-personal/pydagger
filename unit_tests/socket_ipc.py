from pycloak.IPC.stdio import exposed, StdioCom, TCPServer

class Server(StdioCom):

   def __init__(self, address, port):
      super(Server, self).__init__('test', ReaderClass=TCPServer, address=address, port=port)

   @exposed
   def hello(self, *args, **kwargs):
      return (args, kwargs)

srv = Server('127.0.0.1', 7890)
srv.start()
