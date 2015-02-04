from gi.repository import GObject
from threading import Thread
from .events import Event
import pexpect, os, pwd, signal, time, subprocess


class AppMonitor(object):
   def __init__(self, bin_path, on_event=None, label=None):
      if type(on_event) is str: #removeme
         raise Exception('Invalid Type for on_event')
      global on_sig_int
      super(AppMonitor, self).__init__()

      if label is None:
         self.label = bin_path
      else:
         self.label = label

      self.custom_matcher = on_event

      self._monitor = None       #The internal thread instance
      self.bin_path = bin_path   #Application start up command
      self.exec_timeout = None   #Application stop timeout. Defaults to None for no timeout
      self.env = None #dict()    #Environmental variables
      self.on_stopped = Event()  #On application stopped(for any reason) event signal
      self.on_started = Event()  #On application started
      self._is_running = False   #private member, True while application is running
      self.on_started += self._on_started
      self.on_stopped += self._on_stopped

   #callbacks
   @property
   def is_running(self):
      """Returns True if application is currently running"""
      return self._is_running
   def _on_started(self, app):
      self._is_running = True
   def _on_stopped(self, app, failed_start, output):
      self._is_running = False
      self._monitor = None
   def _on_sig_int(self, signal = None, frame = None):
      if self.is_running:
         # clean up before quitting
         self._monitor.kill()
   def start(self):
      """Attempts to start application"""
      if self._monitor == None:
         self._monitor = _AppMonitorThread(self, self.custom_matcher)
         self._monitor.start()
      return self
   def kill_self(self, signal=signal.SIGTERM, blocking=False):
      if self._monitor is not None:
         self._monitor.kill(signal=signal, blocking=blocking)
         self._is_running = False
      return self

class _AppMonitorThread(Thread):
   def __init__(self, app_monitor, matchers):
      if type(matchers) is str: #removeme
         raise Exception('Invalid Type')
      self._app_monitor = app_monitor
      super(_AppMonitorThread, self).__init__()
      self.matchers = matchers
      self._run = True

   def run(self):

      # pre emptive failed start state
      failed_start = True
      output = None
      try:
         child = self.child = pexpect.spawn(
            command  = self._app_monitor.bin_path,
            timeout  = self._app_monitor.exec_timeout,
            env      = self._app_monitor.env,
            ignore_sighup=False)
         failed_start = False # no errors, so did not failed to start

         # trigger start event
         self._on_started(self._app_monitor)

         while self._run:
            child.expect(['(?P<output>[^\r]*\r+)', pexpect.EOF])
            #print child.after

            if child.match == pexpect.EOF: #or not child.isalive():
               self._run = False
               break

            output = child.match.groupdict()['output']
            output = output.decode(encoding='UTF-8')
            #if output == '\n':
            #    continue

            #self.matchers(output)
            if self.matchers is not None:
               GObject.idle_add(lambda output: self.matchers(output), output)

            #print self.child.before
            #time.sleep(2)

         # wait for application to exit
         #self.child.expect(pexpect.EOF)

         output = self.child.before
      except Exception as e:
          print(e)
      finally:
         # trigger stop event even after error
         #for line in self.child:
         #   print line #kk
         self._on_stopped(self._app_monitor, failed_start, output)

   def kill(self, signal=None, blocking=False):
      self.child.terminate(True)
      self.child.close()
      #self.child.kill(signal.SIGTERM)

   def _on_stopped(self, *args, **kwargs):
      if self._app_monitor is not None and self._app_monitor.on_stopped is not None:
         GObject.idle_add(self._app_monitor.on_stopped, *args, **kwargs)

   def _on_started(self, *args, **kwargs):
      if self._app_monitor is not None and self._app_monitor.on_stopped is not None:
         GObject.idle_add(self._app_monitor.on_started, *args, **kwargs)

if __name__ == '__main__':
   on_sig_int = Event()
   signal.signal(signal.SIGINT, lambda *a, **k: on_sig_int(*a, **k))

   on_sig_int += AppMonitor._on_sig_int
   """Guard to kill thread when application exists"""


   from gi.repository import Gtk as gtk
   GObject.threads_init()

   def test_on_started(app):
      print('Application started: %s' % app.label)

   def test_on_stopped(app, failed_start, output):
      print(output)
      print('Application stopped: %s [%s]' % (app.label, 'FAILED' if failed_start else 'NORMAL'))
      gtk.main_quit() # end of test

   def test_on_sig_int(signum = None, frame = None):
      print('Quiting Test')
      os.kill(os.getpid(), signal.SIGKILL)
      gtk.main_quit() # force quit

   def on_out(data):
       print('data: ' + str(data))

   #app = AppMonitor('/usr/bin/firefox', 'Firefox')
   app = AppMonitor('../../data/browser-bundle/start-tor-browser', 'Firefox')

   app.add_matcher(on_out)

   app.env = dict(
      TOR_SKIP_LAUNCH='1',
      TOR_SOCKS_PORT='9069',
      TOR_CONTROL_PORT='9047',
      TOR_CONTROL_PASSWD='"hi"',
      DISPLAY=':0', # passing display info since we are starting firefox from a separate thread without display info
      xhost='local:%s' % (pwd.getpwuid( os.getuid() )[ 0 ]) # also passing current user
   )
   app.on_started += test_on_started
   app.on_stopped += test_on_stopped
   app.start()

   on_sig_int += test_on_sig_int
   gtk.main()

