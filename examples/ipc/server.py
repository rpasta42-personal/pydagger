#!/usr/bin/env python3

from pycloak.IPC.icloakipc import IPCServer, exposed, ExposedAPI

class API(ExposedAPI):

   def __init__(self, session, server):
      super(API, self).__init__("test", session, server)
      self.counter = 0

   @exposed
   def get_string(self):
      self.counter += 1
      return "I am a string! %s" % self.counter

perms=None
address = '/tmp/ipc_example.sock'
print("ADDRESS: %s" % address)
srv = IPCServer.new_unix_transport(address, API, permissions=perms)
srv.start()
