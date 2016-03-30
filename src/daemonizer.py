import os
import sys
import daemon
import lockfile
import traceback

from setproctitle import setproctitle
from pycloak.events import Event
from pycloak.IPC.icloakipc import IPCServer, IPCClient, DisconnectedError

class Daemon(object):

   def __init__(self, sock_address, sock_permissions, proc_title, pidfile, namespace, uid, gid, fork=True):
      self.sock_address = sock_address
      self.sock_permissions = sock_permissions
      self.proc_title = proc_title
      self.pidfile = pidfile
      self.fork = fork
      self.namespace = namespace

      self.on_idle = Event()
      self.on_starting = Event()
      self.on_started = Event()
      self.on_stopping = Event()
      self.on_stopped = Event()

   def start(self):

      daemon_lock = lockfile.FileLock(self.pidfile)
      setproctitle(self.proc_title)
      
      self.on_starting()

      try:
         if self.fork:
            daemon_context.uid = self.uid
            daemon_context.gid = self.gid
            with daemon_context:
               daemon_server = self._setup_daemon_server()
               daemon_server.start()
         else:
            daemon_lock.acquire()
            daemon_server = self._setup_daemon_server()
            daemon_server.start()
      finally:
         daemon_lock.release()

   def _setup_daemon_server(self):
      daemon_server = IPCServer.new_unix_transport(
         address=self.sock_address,
         api_factory=self.get_api_factory(),
         permissions=self.sock_permissions)
      daemon_server.on_idle += self.on_idle
      daemon_server.on_init += self.on_started
      daemon_server.on_stop += self.on_stopped
      return daemon_server

   def get_api_factory(self):
      raise NotImplemented("You must extend this class and implement api factory")

   def get_client(self):
      daemon_client = IPCClient.new_unix_transport(
         address=self.sock_address,
         namespace=self.namespace,
         sync=True)

      try:
         daemon_client.ipc_connect()
         return daemon_client
      except Exception as ex:
         raise ex

   def stop(self):
      self.on_stopping()
      daemon_lock = lockfile.FileLock(self.pidfile)

      try:
         daemon_client = self.get_client()
         with open(self.pidfile, 'r') as pid_fh:
            print(pid_fh.read())

         # client daemon must implement "daemon_stop" method to trigger clean shutdown
         daemon_client.daemon_stop()
      except DisconnectedError as dex:
         pass

      count=0
      while self.status():
         time.sleep(1)
         count += 1
         if count > 5:
            return False

      return True

   def restart(self):
      self.stop()
      self.start()

   def status(self):
      daemon_lock = lockfile.FileLock(self.pidfile)
      if not daemon_lock.is_locked():
         return False
      else:
         return True
