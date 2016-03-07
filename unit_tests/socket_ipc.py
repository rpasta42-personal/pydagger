#!/usr/bin/env python3
import sys
import logging
from pycloak.IPC.icloakipc import exposed, ExposedAPI, IPCServer, TCPTransport, DocGenerator

logging.basicConfig(level=logging.DEBUG)

class TestServer(ExposedAPI):

   def __init__(self, session, server):
      self.on_test_event = self.emitter("test_event")

      super(TestServer, self).__init__('test', session, server)


   @exposed
   def hello(self, first, last):
      self.on_test_event()
      return {'first':first, 'last':last}

   @exposed
   def error_method(self):
      raise Exception("some odd exception")
   

if len(sys.argv) > 1 and  sys.argv[1] == 'server':
   server = IPCServer.new_greentcp_server(
      address='127.0.0.1', 
      port=7890, 
      api_factory=TestServer)
   server.start()
else:
   doc = DocGenerator('test', TestServer)
   print(doc.generate_api('nodejs'))
