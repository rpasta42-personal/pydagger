from os.path import abspath, dirname, realpath
import misc
import configparser

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

class Application(object):
   #_main_file = __file__
   def __init__(self, debug, app_name, _main_app_file):
      super().__init__()
      app_path = abspath(dirname(realpath(_main_app_file)) + '/../')
      in_icloak = misc.file_exists('/etc/icloak')
      if in_icloak:
         debug = False

      if in_icloak:
         conf_path = '/etc/icloak-%s.conf' % app_name
      else:
         conf_path = '%s/data/%ssrc' % (app_path, app_name)

      if misc.file_exists(conf_path):
         conf = misc.read_conf(conf_path)
      else:
         conf =
      self.in_icloak = in_icloak
      self._main_app_file = _main_app_file
      self.debug = debug

