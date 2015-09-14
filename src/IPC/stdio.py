import sys
import time
import json
from jsonrpc import JSONRPCResponseManager, dispatcher

class StdioCom(object):

   def __init__(self, namespace, protocol = "JSONRPC"):
      self.namespace = namespace
      self.run = False
      self._jsonrpc = JSONRPCResponseManager()
      self.protocol = protocol
      # list of callable members
      methods = [ method for method in dir(self) if callable(getattr(self, method)) ]
      for method in methods:
         # get method intance
         m = getattr(self, method)
         # check if its exposed
         if m and hasattr(m, "exposed"):
            dispatcher[method if not namespace else "%s.%s" % (namespace,method)] = m # add it to jsonrpc methods

   def start(self):
      """Main stdio loop"""
      self.run = True
      while self.run:
         self._on_idle()
         time.sleep(0.1)
               
   def _on_idle(self):
      """Handles internal communication parsing"""
      data = None
      try:
         line = sys.stdin.readline()
         if line:
            data = line.strip()
      except:
         pass

      if data:
         if self.protocol == "JSONRPC":
            response = self._jsonrpc.handle(data, dispatcher)
            if response:
               sys.stdout.write("%s\n" % response.json)
               sys.stdout.flush()
            else:
               sys.stdout.write(json.dumps({"error": {"message":"Could not generate response from provided input", "input":data}, "id": None, "jsonrpc": "2.0"}))
               sys.stdout.flush()
         else:
            print("INVALID PROTOCOL: %s" % line)
            self.run = False

      self.on_idle()
   
   def on_idle(self):
      pass

