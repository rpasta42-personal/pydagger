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

def exposed(fn):
    def _exposed(*fargs, **kwargs):
        return fn(*fargs, **kwargs)

    _exposed.exposed = True
    _exposed.exposed_args = [arg for arg in inspect.getargspec(fn).args if arg != "self"]
    return _exposed

class DocGenerator(object):

   def __init__(self, api_factory):
      self.api_factory = api_factory

   def generate_doc(self, lang):
      pass

   def generate_api(self, lang):
      pass

class ProtocolError(Exception):
   def __init__(self, message, code, id=None, data=None):
      self.code = code
      self.message = message
      self.id = id
      self.data = data
      super(ProtocolError, self).__init__()

class InvalidProtocolSyntax(ProtocolError):
   def __init__(self, message="Invalid RPC Syntax", id=None, data=None):
      super(InvalidProtocolSyntax, self).__init__(message, -32700, id, data)

class InvalidProtocolRequest(ProtocolError):
   def __init__(self, message="Invalid Request", id=None, data=None):
      super(InvalidProtocolRequest, self).__init__(message, -32600, id, data)

class MethodNotFound(ProtocolError):
   def __init__(self, message="Method Not Found", id=None, data=None):
      super(MethodNotFound, self).__init__(message, -32601, id, data)

class ServerError(ProtocolError):
   def __init__(self, message, id=None, data=None):
      super(ServerError, self).__init__(message, -32000, id, data)

class Protocol(object):

   def decode_message(self, data):
      assert isinstance(data, bytes), "data to decode should be bytes"
      data_str = str(data, 'ascii')
      try:
         raw = json.loads(data_str)
      except Exception as ex:
         raise InvalidProtocolSyntax()

      return raw.get('id', None), raw.get('method', None), raw.get('params', None), raw.get('result', None), raw.get('error', None)

   def encode_result(self, id, result):
      packet = self.protocol_wrapper(dict(
         result=result,
         id=id))
      return self.encode_bytes(json.dumps(packet))

   def encode_error(self, id, message, data=None):
      packet = self.protocol_wrapper(dict(
         error=dict(code=0, message=message, data=data),
         id=id))
      return self.encode_bytes(json.dumps(packet))
   
   def encode_call(self, id, method, *params):
      packet = self.protocol_wrapper(dict(
         method=method,
         params=list(params),
         id=id))
      return self.encode_bytes(json.dumps(packet))
   
   def encode_exception(self, ex):
      return self.encode_error(ex.id, ex.message, ex.data)

   def protocol_wrapper(self, data):
      assert isinstance(data, dict), "data should be a dict"
      wrapper = dict(jsonrpc="2.0")
      wrapper.update(data)
      return wrapper

   def encode_bytes(self, data):
      return bytes("%s\n" % data, 'ascii')


class ExposedAPI(object):

   def __init__(self, namespace, session, server):
      self.namespace = namespace
      self.session = session
      self.server = server

   def __del__(self):
      pass

   def emitter(self, event):
      """Simple emit method wrapper. Adds event to API registration and
      wraps emit call to better document the event API call."""
      base = self
      def _emit_proxy(*fargs):
         base.emit(event, *fargs)
         LOGGER.debug("EMITTER[%s] %s", event, fargs)
         _emit_proxy.exposed_event = True
      return _emit_proxy

   def emit(self, event, *args):
      self.session.call("@.%s" % event, *args);

   def on_init(self):
      pass

class TCPTransport(object):

   def __init__(self, address, port, listen=1):
      self.address = address
      self.port = port

      self.on_session_added = Event()
      self.on_session_data = Event()
      self.on_session_removed = Event()

      self._server = sockets.TCPServer(address, port, self.on_client_event)
      self._server_update = None
      self._clients = dict()
      self._clients_buffer = dict()

      self._buffer = bytearray()

   def start(self):
      self._server.start()
      self._server_update = self._server.update()

   def update(self):
      next(self._server_update)

   def on_client_event(self, event, client, data=None):
      session_id = "%s:%s" % client.address
      if event == "new_client":
         self._clients[session_id] = client
         self._clients_buffer[session_id] = bytearray()
         self.on_session_added(session_id)
      elif event == "on_data":
         for c in data:
            if c == 10:
               line = bytes(self._clients_buffer[session_id])
               LOGGER.debug(line)
               self.on_session_data(session_id, line)
               del self._clients_buffer[session_id][:]
            else:
               self._clients_buffer[session_id].append(c)

      elif event == "client_left":
         del self._clients[session_id]
         del self._clients_buffer[session_id]
         self.on_session_removed(session_id)

   def send(self, session_id, data):
      assert isinstance(data, bytes) or isinstance(data, bytearray), "Data must be bytes or bytearray"
      assert data != b'null\n', "data can not be null"

      if session_id in self._clients:
         LOGGER.debug("[%s] SEND: %s", session_id, data)
         self._clients[session_id].writer.send(data)
      else:
         LOGGER.error("[%s] SESSION NOT FOUND", session_id)

class IPCSession(object):

   def __init__(self, server, session_id, api_factory, transport, protocol):
      super(IPCSession, self).__init__()

      self.session_id = session_id
      self.api_instance = api_factory(self, server)
      self.transport = transport
      self.protocol = protocol
      self.call_id = 0

   def send(self, data):
      assert isinstance(data, bytes), "data must be bytes"
      self.transport.send(self.session_id, data)

   def call(self, method, *params):
      try:
         self.send(self.protocol.encode_call(self.call_id, method, *params))
      except Exception as ex:
         LOGGER.exception(ex)
      finally:
         self.call_id+=1

   def on_data(self, data):
      prot = self.protocol
      try:
         id, method, args, result, error = self.protocol.decode_message(data)
      except InvalidProtocolSyntax as syntax_exception:
         self.send(prot.encode_exception(syntax_exception))
         LOGGER.exception(syntax_exception)
         return
      except InvalidProtocolRequest as request_exception:
         self.send(prot.encode_exception(request_exception))
         LOGGER.exception(request_exception)
         return

      try:
         if method:

            if args is None:
               args = []

            if self.api_instance.namespace:
               method = method[len(self.api_instance.namespace)+1:]

            if hasattr(self.api_instance, method):
               method_obj = getattr(self.api_instance, method)
               if hasattr(method_obj, 'exposed') and method_obj.exposed:
                  try:
                     result = method_obj(*args)
                     LOGGER.debug("[%s] RESULT: %s", method, result)
                     self.send(prot.encode_result(id=id, result=result))
                  except Exception as ex:
                     self.send(prot.encode_error(id=id, message=str(ex), data=traceback.format_exc()))
                     LOGGER.exception(ex)
                     return
               else:
                  LOGGER.debug("METHOD [%s] FOUND BUT NOT EXPOSED", method)
                  raise MethodNotFound(id=id)
            else:
               LOGGER.debug("METHOD [%s] NOT FOUND", method)
               raise MethodNotFound(id=id)
         elif result:
            pass
         elif error:
            pass
      except MethodNotFound as method_exception:
         self.send(prot.encode_exception(method_exception))
         LOGGER.exception(method_exception)

class IPCServer(object):

   @classmethod
   def new_greentcp_server(cls, address, port, api_factory, protocol_factory=Protocol):
      return cls(api_factory=api_factory, transport=TCPTransport(address, port, listen=1), protocol_factory=protocol_factory)

   @classmethod
   def new_stdio_server(cls, api_factory, protocol_factory=Protocol):
      return cls(api_factory=api_factory, transport=StdIOTransport(), protocol_factory=protocol_factory)

   def __init__(self, api_factory, transport, protocol_factory=Protocol):
      self.transport = transport
      self.protocol_factory = protocol_factory
      self.mqueue = MessageQueue()
      self.api_factory = api_factory
      self._is_running = False
      self._sessions = dict()

      # event listeners for transport session handling
      self.transport.on_session_added += self.on_session_added
      self.transport.on_session_data += self.on_session_data
      self.transport.on_session_removed += self.on_session_removed

   def on_session_added(self, session_id):
      self._sessions[session_id] = IPCSession(self, session_id, self.api_factory, self.transport, self.protocol_factory())

   def on_session_data(self, session_id, data):
      if session_id in self._sessions:
         self._sessions[session_id].on_data(data)
      else:
         LOGGER.error("[ON DATA] Invalid Session ID %s", session_id)

   def on_session_removed(self, session_id):
      del self._session[session_id]

   def start(self):
      """Main stdio loop"""
      self._is_running = True
      self.transport.start()
      self.on_init()
      while self._is_running:
         self.transport.update()

         self.mqueue.process()
         self.on_idle()
         time.sleep(0.1)

   def on_init(self):
      pass

   def on_idle(self):
      pass

   def call(self, method, args, ignore_events=False):
      """Invokes remote methods"""
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

