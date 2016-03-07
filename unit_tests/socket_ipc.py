#!/usr/bin/env python3
import logging
from pycloak.IPC.icloakipc import exposed, ExposedAPI, IPCServer, TCPTransport

logging.basicConfig(level=logging.DEBUG)

class TestServer(ExposedAPI):

   def __init__(self, session, server):
      self.on_test_event = self.emitter("test_event")

      super(TestServer, self).__init__('test', session, server)


   @exposed
   def hello(self, *args, **kwargs):
      self.on_test_event()
      return (args, kwargs)

   @exposed
   def error_method(self):
      raise Exception("some odd exception")
   

server = IPCServer.new_greentcp_server(
   address='127.0.0.1', 
   port=7890, 
   api_factory=TestServer)
server.start()
