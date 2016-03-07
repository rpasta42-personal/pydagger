#!/usr/bin/env python3
import sys
import logging
from pycloak.IPC.icloakipc import exposed, ExposedAPI, IPCServer, IPCClient, DocGenerator, RemoteError

logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s [%(module)s:%(lineno)s] [%(levelname)s] %(message)s)')

class TestServer(ExposedAPI):

   def __init__(self, session, server):
      self.on_test_event = self.emitter("test_event")

      super(TestServer, self).__init__('test', session, server)


   @exposed
   def hello(self, first, last):
      """Just a hello method. It will return an object with the provided first and last fields"""
      self.on_test_event()
      return {'first':first, 'last':last}

   @exposed
   def error_method(self):
      """This method will throw a remote exception to be caught by the client"""
      raise Exception("some odd exception")

if len(sys.argv) > 1:
   if sys.argv[1] == 'server':
      server = IPCServer.new_greentcp_server(
         address='127.0.0.1', 
         port=7890, 
         api_factory=TestServer)
      server.start()
   elif sys.argv[1] == 'client':
      client = IPCClient.new_greentcp_client(
         address='127.0.0.1',
         port=7890,
         namespace='test',
         sync=True)

      def test_event_handler(self):
         print("on test event!")

      client.on('test_event', test_event_handler)
      try:
         client.ipc_connect()

         print(client.ipc_doc('text'))
         print(client.hello('john', 'doe'))
         client.error_method()

      except RemoteError as remote_error:
         print("REMOTE ERROR -------------------")
         print(remote_error)
         print(remote_error.error['data'])
      finally:
         client.ipc_disconnect()
      
else:
   doc = DocGenerator('test', TestServer)
   print(doc.generate_api('nodejs'))
