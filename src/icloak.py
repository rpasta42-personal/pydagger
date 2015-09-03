from os.path import abspath, dirname, realpath
from pycloak import misc #, ConfigParser

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

class Application():
   #_main_file = __file__
   def __init__(self, debug, app_name, main_app_file=None):
      if main_app_file is not None:
         self.app_path = abspath(dirname(realpath(main_app_file)) + '/../') + '/'

      self.main_app_file = main_app_file
      self.in_icloak = misc.file_exists('/etc/icloak')
      self.debug = debug

