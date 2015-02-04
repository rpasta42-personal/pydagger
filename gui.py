from gi.repository import WebKit, Gtk, GObject
if __name__ == '__main__':
   from events import Event
   import misc
else:
   from icloak_lib.events import Event
   from icloak_lib import misc
import json, os

class TrayMenu(object):
   def __init__(self, icon_path, menu_items):
      super(TrayMenu, self).__init__()

      self._menu_items = menu_items
      self._icon = Gtk.StatusIcon() #Gtk.status_icon_new_from_file(icon_path)
      self._icon.set_from_file(icon_path)

      #self._icon.connect('activate', lambda *args: self._make_menu())
      #self._icon.connect('popup-menu', lambda *args: self._make_menu())
      self._icon.connect('button-press-event', lambda widget, event: self._make_menu(widget, event))

   def change_icon(self, new_icon_path):
      self._icon.set_from_file(new_icon_path)

   #event_button=2
   def _make_menu(self, widget, event):
      event_button = event.button
      event_time = event.time

      self.menu = Gtk.Menu()

      for label, handler in self._menu_items:
         item = Gtk.MenuItem(label)
         #handler = self._menu_items[label]
         self.menu.append(item)
         item.connect('activate', handler)

      self.menu.popup(None, None, None, None, event_button, event_time)
      self.menu.show_all()


class Window(object):
   '''Stuff for setting up Gtk + webkit + python'''

   def __init__(self, width, height, title, _visible=True):
      super(Window, self).__init__()

      self.visible = _visible
      self.on_gui_event = Event()
      self.on_gui_event += self._on_resize_hack

      self.width = width
      self.height = height
      self.win = win = Gtk.Window()
      eb = Gtk.EventBox()
      two = Gtk.VBox()
      eb.add(two)
      win.add(eb)
      eb.show()
      
      self.webView = webView = WebKit.WebView()
      #kkkk webView.set_size_request(width, height)
      win.set_default_size(width, height)
      self.webView.props.settings.props.enable_default_context_menu = False
      self.webView.connect('notify::title', self._on_webview_msg)

      self.title = title
      win.set_title(title)
      #win.add(webView)
      two.add(webView)

      self.on_delete = lambda *x: False
      self.win.connect('delete-event', self._on_delete)

      if self.visible:
         self.show()

   def _on_resize_hack(self, json_data): pass 
   def _on_resize_hack_2(self, json_data):
      cmd = json_data['cmd']
      args = json_data['args']
   
      if cmd == 'resize':
         new_height = args['height']
         new_width = args['width']
         print('height: %s, width: %s' % (new_height, new_width))
         self.win.resize(new_height, new_width)


   def _on_delete(self, *args):
      #print 'we got called'
      return self.on_delete()

   def load(self, path):
      path = os.path.realpath(path)
      self.webView.open(path)

   def exec_js(self, code):
      self.webView.execute_script(code)

   def show(self):
      self.win.set_title(self.title)
      self.win.show_all()

   def hide(self):
      #self.win.hide_all()
      self.win.hide()


   def toggle_show(self):
      if self.visible:
         self.hide()
      else:
         self.show()
      self.visible = not self.visible
   def _on_webview_msg(self, v, param):
      raw_data = v.get_title()
      if not raw_data:
         return

      try:
         data = json.loads(raw_data)
      except Error as ex:
         pass

      assert data['_magic'] == 'gentoo-sicp-wizards'

      if self.on_gui_event is not None:
         self.on_gui_event(data)
   #Optional. Can also use custom loop
   def run(self, main_loop_callback=None, how_often=1000):
      if main_loop_callback == None:
         main_loop_callback = lambda:None

      def main_loop_updater():
         main_loop_callback()
         GObject.timeout_add(how_often, main_loop_updater)

      main_loop_callback()
      #Gtk.main()

if __name__ == '__main__':
   w = Window(300, 200, 'hi', True)
   w.load('/tmp/test.html')
   Gtk.main()

