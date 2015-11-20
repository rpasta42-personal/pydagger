import json
from pycloak import shellutils

#same as raise but can be used as function
#def throw(err): raise err
#def is_error(x): return isinstance(x, Error)

#initialized in init() and used by Error
#_handle_error = lambda *args: throw('need to initialize misc first')


###small misc toools###

def logical_xor(str1, str2):
    return bool(str1) ^ bool(str2)

def nothing_proc(*args):
   return args

def run_periodically(seconds, func):
   gobject.timeout_add(seconds*1000, func)



if 0 == 1:
   from gi.repository import Gtk
   import notify2 as pynotify
   import os

   def init_pynotify(prog_name):
      pynotify.init(prog_name)
      #gobject.threads_init()

   def notify(title, msg='', pic='onion', timeout=pynotify.EXPIRES_DEFAULT):
      #if pic == 'icloak':
      #   pic_path = '%s/data/tor_logo.png' % os.getcwd()

      if pic == 'default-warn':
         pic_path = 'dialog-warning'
      elif pic == 'onion-png':
         pic_path = '%s/data/onion.png' % os.getcwd()
      elif pic != None:
         pic_path = '%s/data/%s.svg'  % (os.getcwd(), pic)

      if pic == None:
         n = pynotify.Notification(title, msg)
      else:
         n = pynotify.Notification(title, msg, pic_path)

      n.set_timeout(timeout) #1000=1 sec
      #n.set_urgency(pynotify.URGENCY_CRITICAL)

      if not n.show():
         raise Exception('could not send notification')

      return n

   def update_notification(n, title, msg, pic, timeout=None):
      n.update(title, msg, pic)
      if timeout:
         n.set_timeout(timeout)
         pass

   def alert(data=None):
      msg = Gtk.MessageDialog(None, Gtk.DIALOG_MODAL, Gtk.MESSAGE_INFO, Gtk.BUTTONS_OK, data)
      msg.run()
      msg.destroy()

