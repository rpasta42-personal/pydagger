#!/usr/bin/env python3

from pycloak.IPC.icloakipc import IPCClient
import time

client = IPCClient.new_unix_transport(
   address='/tmp/ipc_example.sock', 
   namespace='test', 
   sync=True)

client.ipc_connect()

while 1:
   print(client.get_string())
   time.sleep(5)
