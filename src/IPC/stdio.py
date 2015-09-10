import sys
import time
from jsonrpc import JSONRPCResponseManager, dispatcher

class StdioCom(object):

   def __init__(self, namespace):
      self.namespace = namespace
      self.run = False
      self._jsonrpc = JSONRPCResponseManager()
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
      line = None
      try:
         line = sys.stdin.readline()
         line = line.strip()
      except:
         pass

      if line:
         parts = line.split(" ", 1)
         if len(parts) > 0:
            protocol = parts[0]
         if len(parts) > 1:
            data = parts[1]

         if protocol == "JSONRPC":
            response = self._jsonrpc.handle(data, dispatcher)
            print(response.json)
         elif protocol == 'exit':
            self.run = False
         else:
            print("INVALID PROTOCOL: %s" % line)
            self.run = False

      self.on_idle()
   
   def on_idle(self):
      pass

