"""Simple IPC server/client api for ICLOAK platform"""
import time
import json
import traceback
import inspect
import socket
import textwrap
import logging

from pycloak.events import Event
from pycloak.threadutils import MessageQueue
from pycloak import sockets

LOGGER = logging.getLogger(__name__)

def exposed(fn):
    def _exposed(*fargs, **kwargs):
        return fn(*fargs, **kwargs)

    _exposed.__doc__ = fn.__doc__
    _exposed.exposed = True
    _exposed.exposed_args = [arg for arg in inspect.getfullargspec(fn).args \
        if arg != "self"]
    return _exposed

class DocGenerator(object):

    def __init__(self, namespace, api_factory, transport='UnixIOLib', transport_args='address'):
        self.namespace = namespace
        self.api_factory = api_factory
        self.api_instance = api_factory(namespace, None)
        self.transport = transport
        self.transport_args = transport_args
        self.method_join_char = "\n\n"
        self.methods = dict()
        members = [ member for member in dir(self.api_instance) \
            if callable(getattr(self.api_instance, member)) ]

        for member in members:
            # get method intance
            m = getattr(self.api_instance, member)
            # check if its exposed
            if m and hasattr(m, "exposed"):
                self.methods[member] = m

    def generate_doc(self, format):
        if format in ("dict", "json"):
            self.method_join_char = ','
        return self._api_generator(format, "doc")

    def generate_api(self, lang):
        return self._api_generator(lang, "api")

    def _api_generator(self, lang, generator):
        g_start = getattr(self, "_generate_%s_start" % generator)
        g_method = getattr(self, "_generate_%s_method" % generator)
        g_end = getattr(self, "_generate_%s_end" % generator)

        # list of callable members
        methods = self.methods
        api_src = []
        api_src.append(g_start(lang))
        for method in methods:
            m = getattr(self.api_instance, method)
            # check if its exposed
            if m and hasattr(m, "exposed"):
                if hasattr(m, "exposed_args"):
                    args = m.exposed_args
                else:
                    args = [arg for arg in inspect.getargspec(m).args if arg != "self"]
                doc_str = inspect.getdoc(m)
                if doc_str == None:
                    doc_str = ""
                api_src.append(g_method(lang, method, args, doc_str))
            elif m and hasattr(m, "exposed_raw"):
                if hasattr(m, "exposed_args"):
                    args = m.exposed_args
                else:
                    args = [arg for arg in inspect.getargspec(m).args if arg != "self"]
                doc_str = inspect.getdoc(m)
                if doc_str == None:
                    doc_str = ""
                api_src.append(g_method(lang, method, args, doc_str, m))


        api_src.append(g_end(lang))
        if lang not in ('dict', 'json'):
            result = self.method_join_char.join(api_src)
        else:
            result = api_src[0] + self.method_join_char.join(api_src[1:-1]) + api_src[-1]

        if lang in ('dict'):
            result = json.loads(result)

        return result

    def _generate_api_start(self, lang):
        if lang in ["nodejs"]:
            return """'use strict';
module.exports = (function() {
     var util = require('util');
     var EventEmitter = require('events').EventEmitter;
     var icloakipc = require("icloakipc");

     var %(namespace)s = function(%(init_args)s, options) {
          this._transport = new icloakipc.%(transport)s(%(init_args)s, options);
          this._rpc = new icloakipc.jsonrpc(this._transport, "%(namespace)s");
          var base = this;
          this._rpc.on("connected", function() {
              base.emit("connected");
          });
          this._rpc.on("error", function(error) {
                base.emit("error", error);
          });
          this._rpc.on("emit", function(evt, args) {
                var combined_args = [evt].concat(args);
                base.emit.apply(base, combined_args);
          });
     }

     // Inherit event emitter functionality
     util.inherits(%(namespace)s, EventEmitter); //updater

     // Start transport
     %(namespace)s.prototype.start = function() { //updater
          this._transport.start()
     }
     // kills the child process
     %(namespace)s.prototype.kill = function(n) {
          this._transport.kill(n)
     }
""" % dict(namespace=self.namespace, transport=self.transport, init_args=self.transport_args)
        elif lang in ["javascript"]:
            return "var %s = function(rpc) { this._rpc = rpc; }" % self.namespace

        return ""

    def _generate_api_method(self, lang, method, args, doc, raw = None):
        if lang in ["javascript", "nodejs"]:
            space = ""
            if lang == "nodejs":
                space = "     "
            out = ""
            args_call = []
            for arg in args:
                args_call.append("'%s': %s" % (arg, arg))


            if raw is None:
                body = "return this._rpc.call('%s', {%s});" % (method, ", ".join(args_call))
            else:
                body = raw()

            if doc:
                doc = "%s/**\n%s\n%s */\n" % (space, "\n".join(["%s * %s" % (space, line) for line in doc.splitlines()]), space)
            else:
                doc = ""

            return "%s%s%s.prototype.%s = function(%s) { %s }" % (doc, space, self.namespace, method, ", ".join(args), body)

        return ""

    def _generate_api_end(self, lang):
        if lang == "javascript":
            return ""
        elif lang == "nodejs":
            return """     return %(namespace)s;
}());""" % dict(namespace=self.namespace)

        return ""

    def _generate_doc_start(self, format):
        if format == "html":
            style = """
html, body { width: 100%; height: 100%; padding: 0; margin: 0; }
.method { padding: 0 0 2em 2em; border-bottom: 1px solid #000; }
.method .name { color: green; text-weight: bolder; }
.method .arg { color: red; }
.method .doc { padding-left: 4em; }
"""
            return '<!doctype html><html><head><title>%(namespace)s Documentation</title><style type="text/css">%(style)s</style></head><body><div class="namespace">%(namespace)s</div>' % dict(namespace=self.namespace, style=style)
        elif format in ("dict", "json"):
            return "{"

        return ""

    def _generate_doc_method(self, format, method, args, doc, raw=None):

        if format == "text":
            args_txt = ", ".join(args)
            doc_txt = "\n".join(textwrap.wrap(doc, width=40, initial_indent=' ' * 4, subsequent_indent=' ' * 4))
            #doc_txt = "%s\n" % doc_txt if len(doc_txt) > 0 else ""
            return '%(method)s(%(args)s)\n%(doc)s' % dict(method=method, args=args_txt, doc=doc_txt)

        if format == "html":
            args_txt = ['<span class="arg">%s</span>' % arg for arg in args]
            return """<div class="method">
                        <span class="name">%(method)s</span>
                        (<span class="args">%(args)s</span>)
                        <div class="doc">%(doc)s</div></div>""" % \
                        dict(method=method, args=", ".join(args_txt), doc=doc)

        if format in ("dict", "json"):
            return '"%s": %s ' % (method,
                json.dumps(dict(
                    method=method,
                    params=args,
                    doc=doc))
            )
        return ""

    def _generate_doc_end(self, format):
        if format == "html":
            return "</body></html>"
        if format in ("dict", "json"):
            return "}"

        return ""

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
    def __init__(self, message="Method Not Found", method="", id=None, data=None):
        message=message + " : %s" % method
        super(MethodNotFound, self).__init__(message, -32601, id, data)

class ServerError(ProtocolError):
    def __init__(self, message, id=None, data=None):
        super(ServerError, self).__init__(message, -32000, id, data)

class RemoteError(Exception):
    def __init__(self, error):
        self.error = error
        super(RemoteError, self).__init__(error['message'])

class DisconnectedError(Exception):
    pass

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
        self.session.call("@.%s" % event, *args)

    def on_init(self):
        pass

    @exposed
    def ipc_doc(self, format='text'):
        """Returns documentation about this remote object. Defaults to text format"""
        doc = DocGenerator(self.namespace, lambda a,b: self)
        return doc.generate_doc(format)

class SocketClientTransport(object):

    @classmethod
    def new_tcp_transport(cls, ip, port):
        return cls((ip, port), socket_type=socket.AF_INET)

    @classmethod
    def new_unix_transport(cls, address):
        return cls(address, socket_type=socket.AF_UNIX)

    def __init__(self, address, socket_type=None):
        assert socket_type is not None, "Socket type is invalid"

        self.address = address
        self.socket_type = socket_type
        self._buffer = bytearray()
        self._client = None

        self.on_data = Event()
        self.on_connected = Event()

    def connect(self):
        self._buffer = bytearray()
        self._client = sockets.SocketClient(
            self.address,
            self.on_client_event,
            socket_type=self.socket_type)
        self._client.connect()

    def disconnect(self):
        try:
            if self._client:
                self._client.disconnect()
        except Exception as ex:
            pass

    def update(self):
        if self._client:
            return self._client.update()
        return False

    def on_client_event(self, event, client, data=None):
        if event == "on_connected":
            self.on_connected(self)
        elif event == "on_data":
            for c in data:
                if c == 10:
                    LOGGER.debug(bytes(self._buffer))
                    self.on_data(self, bytes(self._buffer))
                    del self._buffer[:]
                else:
                    self._buffer.append(c)

    def send(self, data):
        assert isinstance(data, bytes), 'data must be bytes'
        self._client.writer.send(data)

class SocketServerTransport(object):

    @classmethod
    def new_tcp_transport(cls, ip, port, listen=1):
        return cls((ip, port), listen, socket_type=socket.AF_INET)

    @classmethod
    def new_unix_transport(cls, address, listen=1, permissions=None):
        return cls(address, listen, socket_type=socket.AF_UNIX, permissions=permissions)

    def __init__(self, address, listen=1, socket_type=None, permissions=None):
        self.address = address
        self.listen = listen
        self.socket_type = socket_type
        self.permissions = permissions

        self.on_session_added = Event()
        self.on_session_data = Event()
        self.on_session_removed = Event()

        self._server_update = None
        self._clients = dict()
        self._clients_buffer = dict()
        self._buffer = bytearray()

    def __del__(self):
        self.stop()

    def start(self):
        self._clients = dict()
        self._clients_buffer = dict()
        self._buffer = bytearray()

        self._server = sockets.SocketServer(
            self.address,
            self.on_client_event,
            listen=self.listen,
            socket_type=self.socket_type,
            permissions=self.permissions)

        self._server.start()
        self._server_update = self._server.update()

    def stop(self):
        if self._server:
            self._server.stop()
            self._server = None

    def update(self):
        next(self._server_update)

    def on_client_event(self, event, client, data=None):
        session_id = str(client)
        if event == "new_client":
            self._clients[session_id] = client
            self._clients_buffer[session_id] = bytearray()
            self.on_session_added(session_id)
        elif event == "on_data":
            for c in data:
                if c == 10:
                    line = bytes(self._clients_buffer[session_id])
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
            self._clients[session_id].writer.send(data)
        else:
            LOGGER.error("[%s] SESSION NOT FOUND", session_id)

class IPCSession(object):
    """IPC Session class. Handles states between client connection sessions"""

    def __init__(self, server, session_id, api_factory, transport, protocol):
        super(IPCSession, self).__init__()

        self.session_id = session_id
        self.api_instance = api_factory(self, server)
        self.transport = transport
        self.protocol = protocol
        self.call_id = 0

    def send(self, data):
        """Sends raw bytes"""
        assert isinstance(data, bytes), "data must be bytes"
        self.transport.send(self.session_id, data)

    def call(self, method, *params):
        """Performs a remote method call"""
        try:
            LOGGER.debug("REMOTE CALL: %s(%s)", method, params)
            self.send(self.protocol.encode_call(self.call_id, method, *params))
        except Exception as ex:
            LOGGER.exception(ex)
        finally:
            self.call_id+=1

    def on_data(self, data):
        """Handles receiving raw byte line data. Where each message is split
        with a new line byte(10) \\n"""

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
            orig_method = method
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
                            LOGGER.error("REMOTE ERROR: %s\n%s",
                                str(ex), traceback.format_exc())
                            self.send(prot.encode_error(
                                id=id,
                                message=str(ex),
                                data=traceback.format_exc()))

                            return
                    else:
                        LOGGER.debug("METHOD [%s] FOUND BUT NOT EXPOSED", orig_method)
                        raise MethodNotFound(id=id, method=orig_method)
                else:
                    LOGGER.debug("METHOD [%s] NOT FOUND", orig_method)
                    raise MethodNotFound(id=id, method=orig_method)
            elif result:
                pass
            elif error:
                pass
        except MethodNotFound as method_exception:
            self.send(prot.encode_exception(method_exception))
            LOGGER.exception(method_exception)

class IPCServer(object):
    """IPC Server class. To be used to provide service APIs"""

    @classmethod
    def new_tcp_transport(cls, ip, port, api_factory, protocol_factory=Protocol):
        return cls(api_factory=api_factory, transport=SocketServerTransport.new_tcp_transport(ip, port, listen=1), protocol_factory=protocol_factory)

    @classmethod
    def new_unix_transport(cls, address, api_factory, protocol_factory=Protocol, permissions=None):
        return cls(api_factory=api_factory, transport=SocketServerTransport.new_unix_transport(address, listen=1, permissions=permissions), protocol_factory=protocol_factory)

    def __init__(self, api_factory, transport, protocol_factory=Protocol):
        self.transport = transport
        self.protocol_factory = protocol_factory
        self.mqueue = MessageQueue()
        self.api_factory = api_factory
        self._is_running = False
        self._blocking = True
        self._sessions = dict()
        self.on_idle = Event()
        self.on_init = Event()
        self.on_stop = Event()

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
        del self._sessions[session_id]

    def start(self, blocking=True):
        """Main icloakipc loop"""
        self._is_running = True
        self._blocking = blocking
        self.transport.start()
        self.on_init(self)
        if self._blocking:
            while self._is_running:
                self.update()
                time.sleep(0.01)
            self.on_stop(self)
            self._is_running = False

    def trigger(self, event, *args):
        for session_id, session in self._sessions.items():
            session.call('@.' + event, *args)

    def update(self):
        if self._is_running:
            self.transport.update()
            self.mqueue.process()
            self.on_idle(self)

    def stop(self):
        self._is_running = False
        self.transport.stop()
        if not self._blocking:
            self.on_stop(self)


class IPCClient(object):

    @classmethod
    def new_tcp_transport(cls, ip, port, namespace=None, protocol_factory=Protocol, sync=False):
        return cls(
            transport=SocketClientTransport.new_tcp_transport(ip, port),
            namespace=namespace,
            protocol_factory=protocol_factory,
            sync=sync)

    @classmethod
    def new_unix_transport(cls, address, namespace=None, protocol_factory=Protocol, sync=False):
        return cls(
            transport=SocketClientTransport.new_unix_transport(address),
            namespace=namespace,
            protocol_factory=protocol_factory,
            sync=sync)

    def __init__(self, transport, namespace=None, protocol_factory=Protocol, sync=False, ignore_missing_events=True):
        self._transport = transport
        self._protocol = protocol_factory()
        self._send_id = 0
        self.namespace = namespace
        self._sync = sync
        self._ignore_missing_events = ignore_missing_events

        self.ipc_on_connected = Event
        self.ipc_on_disconnected = Event #TODO: test for disconnection

        self._transport.on_data += self.__on_data
        self._transport.on_connected += self.__on_connected
        self._events = dict()

        self._event_handlers = dict()

    def ipc_connect(self):
        self._transport.connect()

    def ipc_disconnect(self):
        self._transport.disconnect()

    def ipc_update(self):
        if not self._transport.update():
            raise DisconnectedError()

    def on(self, event, callback):
        if event not in self._event_handlers:
            self._event_handlers[event] = Event()
        self._event_handlers[event] += callback

    def trigger(self, event, *args):
        if event in self._event_handlers:
            self._event_handlers[event](*args)
        elif not self._ignore_missing_events:
            LOGGER.error("Event handler not found: %s", event)
            raise MethodNotFound(id='event', method=event)

    def __getattr__(self, name):
        def _fn(*args):
            method = name if self.namespace is None else "%s.%s" % (self.namespace, name)
            packet = self._protocol.encode_call(self._send_id, method, *args)
            event = IPCEvent(self._send_id, self)
            self._events[self._send_id] = event
            self._send_id += 1
            self._transport.send(packet)
            if self._sync:
                return event.wait()
            else:
                return event

        return _fn

    def __on_data(self, _, data):
        try:
            id, method, args, result, error = self._protocol.decode_message(data)
        except InvalidProtocolSyntax as syntax_exception:
            LOGGER.exception(syntax_exception)
            raise syntax_exception
        except InvalidProtocolRequest as request_exception:
            LOGGER.exception(request_exception)
            raise request_exception

        if method:

            if not args:
                args = []

            if method[0] == '@':
                try:
                    self.trigger(method[2:], *args)
                except MethodNotFound as mex:
                    raise mex
                except Exception as ex:
                    LOGGER.exception(ex)
            else:
                LOGGER.error("METHOD NOT EXPOSED/FOUND: %s", method)
                raise MethodNotFound(id=id, method=method)


        elif result is not None:
            if id in self._events:
                self._events[id].on_result(result)
                del self._events[id]
        elif error is not None:
            if id in self._events:
                self._events[id].on_error(error)
                del self._events[id]

    def __on_connected(self, transport):
        self.ipc_on_connected(self)

class IPCEvent(object):

    def __init__(self, id, client):
        self.id = id
        self.on_result = Event()
        self.on_error = Event()
        self._client = client

    def wait(self, timeout=-1):
        self._wait_success = None
        self.on_result += self._on_wait_result
        self.on_error += self._on_wait_error
        start_time = time.time()
        while self._wait_success is None:
            try:
                self._client.ipc_update()
            except DisconnectedError as dex:
                raise dex

            elapsed_time = time.time() - start_time
            if timeout > -1 and elapsed_time > timeout:
                raise TimeoutError()
            time.sleep(0.01)

        if self._wait_success:
            return self._wait_result
        else:
            raise RemoteError(self._wait_error)

    def _on_wait_result(self, result):
        self._wait_result = result
        self._wait_success = True

    def _on_wait_error(self, error):
        self._wait_error = error
        self._wait_success = False
