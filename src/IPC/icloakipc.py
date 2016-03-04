import sys
import time
import json
import uuid
import traceback
import inspect
import textwrap
import threading

from pprint import pprint, pformat
from pycloak.events import Event
from pycloak.threadutils import MessageQueue
from pycloak import sockets

import logging
LOGGER = logging.getLogger(__name__)

class TCPServer(threading.Thread):

   def __init__(self, com, address, port):
      self._client = sockets.TCPServer(address, port, self._handler)
      self._com = com
      self._buffer = bytearray()
      self._runnign = False
      super(TCPReader, self).__init__()

   def _handler(self, e, data=None):
      if e == "on_data":
         for byte in data:
            if byte != "\n":
               self._buffer.append(byte)
               line = str(bytes(self._buffer), 'ascii')
               line = line.strip()
               self._com.mqueue.invoke(self._com._on_data, line)
            else:
               self._buffer = bytearray()

   def run(self):
      self._running = True
      try:
         self._client.connect()
         while self._running:
            self._client.update()
            time.sleep(0.1)
      except Exception as ex:
         LOGGER.exception(ex)
      self._running = False

def exposed(fn):
    def _exposed(*fargs, **kwargs):
        fn(*fargs, **kwargs)

    _exposed.exposed = True
    _exposed.exposed_args = [arg for arg in inspect.getargspec(fn).args if arg != "self"]
    return _exposed

class ApiGenerator(object):

   def __init__(self, apiClass):
      self.apiClass = apiClass

   def generate_doc(self, lang):
      pass

   def generate_api(self, lang):
      pass

class Protocol(object):

   def (self, message):
      pass

   def decode(self, message):
      pass

class ExposedAPI(object):

   def __init__(self, namespace, reader, writer):
      self.namespace = namespace
      self.on_call_error = Event()
      # list of callable members
      methods = [ method for method in dir(self) if callable(getattr(self, method)) ]
      for method in methods:
         # get method intance
         m = getattr(self, method)
         # check if its exposed
         if m and hasattr(m, "exposed"):
            self.dispatcher[method if not namespace else "%s.%s" % (namespace,method)] = m # add it to jsonrpc methods

   def __del__(self):
      pass

   def create_emitter(self, event):
      """Simple emit method wrapper. Adds event to API registration and
      wraps emit call to better document the event API call."""
      base = self
      def _emit_proxy(*fargs):
         base.emit(event, *fargs)
         LOGGER.debug("[%s] %s", event, fargs)
         _emit_proxy.exposed_event = True
      return _emit_proxy

   def emit(self, event, *args):
      self.call("@.%s" % event, list(args));

   def on_init(self):
      pass

class TCPTransport(object):

   def __init__(self, address, port):
      self.address = address
      self.port = port

      self.on_session_added = Event()
      self.on_session_data = Event()
      self.on_session_removed = Event()

      self.__server = sockets.TCPServer(address, port, self.on_client_event)

   def start(self):
      self.__server.start()

   def update(self):
      next(self.__server.update())

   def on_client_event(self, event, client, data=None):
      session_id = client.address+":"+str(client.port)
      if self.event == "new_client":
         self.on_session_added(session_id)
      elif self.event == "on_data":
         self.on_session_data(session_id, data)
      elif self.event == "client_left":
         self.on_session_removed(session_id)

class IPCSession(object):

   def __init__(self, apiInstance, transport, protocol):
      super(IPCSession, self).__init__()

      self.transport = transport
      self.protocol = protocol

   def on_data(self, data):
      # TODO: keep track of invoke id
      id, method, args = self.protocol.decode(data)

   def respond(self, invoke_id, result):
      pass

   def send_error(self, error):
      pass

class IPCServer(object):

   @classmethod
   def new_greentcp_server(cls, address, port, apiClass, protocolClass=Protocol):
      return cls(apiClass=apiClass, transport=TcpServer(address, port, listen=1), protocolClass=protocolClass)

   @classmethod
   def new_stdio_server(cls, apiClass, protocolClass=Protocol):
      return cls(apiClass=apiClass, transport=StdIOTransport(), protocolClass=protocolClass)

   def __init__(self, apiClass, transport, protocolClass=Protocol):
      self.transport = transport
      self.protocolClass = protocolClass
      self.mqueue = MessageQueue()
      self.__is_running = False
      sekf._sessions = dict()

      self.transport.on_session_added += self.on_session_added
      self.transport.on_session_data += self.on_session_data
      self.transport.on_session_removed += self.on_session_removed

   def on_session_added(self, session_id)
      self._sessions[session_id] = IPCSession(self, self.transport, self.protocolClass())

   def on_session_data(self, session_id, data):
      if session_id in self._sessions:
         self._sessions[session_id].on_data(data)
      else:
         LOGGER.error("[ON DATA] Invalid Session ID %s", session_id)

   def on_session_removed(self, session_id):
      del self._session[session_id]

   def start(self):
      """Main stdio loop"""
      self.__is_runnign = True
      self.transport.start()
      self.on_init()
      while self.__is_running:
         for session in self._sessions:
            session.update()

         self.mqueue.process()
         self.__on_idle()
         time.sleep(0.1)

   def __on_data(self, data):
      if data:
         if self.protocol == "JSONRPC":
            try:
               data_json = json.loads(data)

            except:
               self._send_error(code=-32700, message="Invalid json data", data=traceback.format_exc(), id=None)
               return

            if "result" in data_json or "error" in data_json:
               self._handle_client_response(data_json)
               return

            method = data_json.get("method", None)
            params = data_json.get("params", None)
            id = data_json.get("id", None)

            LOGGER.info('[client] %s(%s)' % (method, params))
            if method is None or params is None:
               self._send_error(code=-32600, message ="Invalid Request", id=id)
            elif self.dispatcher.get(method, None) == None:
               self._send_error(code=-32601, message = "Method Not Found", id=id)
            else:
               try:
                  result = self.dispatcher[method](**params)
                  self._send(json.dumps(dict(jsonrpc="2.0", result=result, id=id)))
               except:
                  exc_type, exc_value, exc_traceback = sys.exc_info()
                  #exception_list = traceback.format_stack()
                  exc_str = traceback.format_exc()
                  #self._send_error(code=-32000, message = str(exc_value), data = "\n".join(exception_list), id=id)
                  self._send_error(code=-32000, message = str(exc_value), data = exc_str, id=id)
                  LOGGER.error('Exception type: %s; Exception value: %s' %(exc_type, exc_value))
                  LOGGER.error(exc_str)

         else:
            print("INVALID PROTOCOL: %s" % line)
            self.run = False

      self.on_idle()


   def stop(self):
      """Stops stdio loop"""
      self.run = False

   def call(self, method, args, ignore_events=False):
      """Performs rpc methods"""
      evt = dict(on_result=Event(), on_error=Event())
      try:
         package = dict(jsonrpc="2.0", method=method, params=args)
         if method[0] != '@':
            package['id'] = self._send_id
         if not ignore_events:
            self._send_events["e%s" % self._send_id] = evt
         self._send(json.dumps(package))
      except:
         if not ignore_events:
            self._send_events.pop("e%s" % self._send_id, None)
         return False
      finally:
         self._send_id+=1

      if not ignore_events:
         return evt

   def _handle_client_response(self, data):
      """Handles replies from client"""
      if "id" in data:
         # get and remove event if available
         evt = self._send_events.pop("e%s" % data["id"], None)

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

   def __on_idle(self):
      """Handles internal communication parsing"""
      self.on_idle()

   def on_idle(self):
      pass
