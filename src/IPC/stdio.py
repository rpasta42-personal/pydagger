import sys
import time
import json
import traceback
import inspect
from pprint import pprint, pformat
from jsonrpc import JSONRPCResponseManager, dispatcher
from pycloak.events import Event

class StdioClient(object):

   def __init__(self, server):
      self._server = server

   def __getattr__(self, name):

      server = self._server
      def proxymethod(*args, **kwargs):
         if args and len(args) > 0:
            raise NotImplementedError("Only arguments by name are allowed")
         return server.call(name, kwargs)

      return proxymethod

class StdioCom(object):

   def __init__(self, namespace, protocol = "JSONRPC"):
      self.namespace = namespace
      self.run = False
      self._jsonrpc = JSONRPCResponseManager()
      self._send_id=0
      self.protocol = protocol
      self._send_events = {}
      self.on_call_error = Event()
      self.client = StdioClient(self)
      # list of callable members
      methods = [ method for method in dir(self) if callable(getattr(self, method)) ]
      for method in methods:
         # get method intance
         m = getattr(self, method)
         # check if its exposed
         if m and hasattr(m, "exposed"):
            dispatcher[method if not namespace else "%s.%s" % (namespace,method)] = m # add it to jsonrpc methods

   def generate_api(self, lang):
      
      api = []
      api.append("""var %s = function(rpc) {
      this._rpc = rpc;
}""" % self.namespace)
      method_docs = dict()
      # list of callable members
      methods = [ method for method in dir(self) if callable(getattr(self, method)) ]
      for method in methods:
         # get method intance
         m = getattr(self, method)
         # check if its exposed
         if m and hasattr(m, "exposed"):
            doc = inspect.getdoc(m)
            arg_spec = inspect.getargspec(m)
            args = []
            args_call = []
            for arg in arg_spec.args:
               if arg != "self":
                  args.append(arg)
                  args_call.append("'%s': %s" % (arg, arg))

            args = ", ".join(args)
            body = "return this._rpc.call('%s', {%s});" % (method, ", ".join(args_call))
            if doc:
               doc = "/**\n%s\n */\n" % ("\n".join([" * %s" % line for line in doc.splitlines()]))
            api.append("%s%s.prototype.%s = function(%s) { %s }" % (doc, self.namespace, method, args, body))
         
      return "\n\n".join(api)

   def generate_doc(self, format):
      return ""

   def start(self):
      """Main stdio loop"""
      self.run = True
      while self.run:
         self._on_idle()
         time.sleep(0.1)

   def call(self, method, args):
      evt =dict(on_result=Event(), on_error=Event())
      try:
         package = dict(jsonrpc="2.0", method=method, params=args, id=self._send_id)
         self._send_events["e%s" % self._send_id] = evt 
         self._send(json.dumps(package))
      except:
         self._send_events.pop("e%s" % self._send_id, None)
         return False
      finally:
         self._send_id+=1

      return evt

   def _handle_client_response(self, data):
      """Handles replies from client"""
      if "id" in data:
         # get and remove event if available
         evt = self._send_event.pop("e%s" % data["id"], None)

      if "result" in data:
         if evt and "on_result" in evt:
            try:
               evt["on_result"](data["result"])
            except:
               pass

      elif "error" in data:
         if evt and "on_error" in evt:
            try:
               evt["on_error"](data["error"])
            except:
               pass
         else:
            self.on_call_error(data["error"])

   def _send(self, data):
      sys.stdout.write("%s\n" % data)
      sys.stdout.flush()

   def _send_error(self, code, message, data, id):
      package = dict(jsonrpc="2.0", error=dict(code=code, message=message, data=data), id=id)
      self._send(json.dumps(package))
               
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
            try:
               data_json = json.loads(data)
            except:
               self._send_error(code=-32700, message="Invalid json data", data=traceback.format_exc(), id=None)
               return

            if "result" in data_json or "error" in data_json:
               self._handle_client_result(data_son)
               return

            response = self._jsonrpc.handle(data, dispatcher)
            if response:
               self._send(response.json)
            else:
               seld._send_error(code=-32600, message ="Could not generate response from provided input", data=data, id=None)
         else:
            print("INVALID PROTOCOL: %s" % line)
            self.run = False

      self.on_idle()
   
   def on_idle(self):
      pass

