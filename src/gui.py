from gi.repository import WebKit, Gtk, GObject
from events import Event
import misc, json, os

#TODO: make all window inherit from this class (instead of having it as member element)
class Window(object):
   '''Stuff for setting up Gtk + webkit + python'''

   def __init__(self, width, height, title, _visible=True, debug = False):
      super(Window, self).__init__()

      self.visible = _visible
      self.on_gui_event = Event()

      self.width = width
      self.height = height
      self.win = win = Gtk.Window()

      self.wk = wk = WebKit.WebView()
      self.wkSettings = wkSettings = self.wk.get_settings()

      self.wk.connect('notify::title', self._on_webview_msg)

      self.title = title
      win.set_title(title)
      win.set_default_size(width, height)

      self.box = Gtk.VBox()
      self.box.pack_start(wk, True, True, 0)

      #look through Felipe's webkit code on launcher.
      #wk.set_property('enable-file-access-from-file-uris', True)
      #wk.set_property('enable-accelerated-compositing', True)
      #wk.set_property('enable-xss-auditor', False)

      props = wk.props.settings.props
      props.enable_default_context_menu = False
      if debug:
         props.enable_default_context_menu = True
         def open_inspector(inspector, target_view):
            inspector_view = WebKit.WebView()
            self.box.pack_start(inspector_view, True, True, 0)
            return inspector_view
         wkSettings.set_property('enable-developer-extras', True)
         inspector = wk.get_inspector()
         inspector.connect('inspect-web-view', open_inspector)


      scrolled_win = Gtk.ScrolledWindow()
      #scrolled_win.set_policy(
      scrolled_win.add_with_viewport(self.box)

      win.add(scrolled_win)
      #win.add(self.box)

      self.on_delete = lambda *x: False
      self.win.connect('delete-event', self._on_delete)

      if self.visible:
         self.show()

   def _on_delete(self, *args):
      #print('we got called')
      return self.on_delete()

   def load(self, path):
      path = os.path.realpath(path)
      self.wk.open(path)

   def exec_js(self, code):
      self.wk.execute_script(code)

   def show(self):
      self.win.set_title(self.title)
      self.win.show_all()

   def hide(self):
      #self.win.hide_all()
      self.win.hide()

   def maximize(self):
      self.win.maximize()

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
      Gtk.main()


class TrayMenu(object):
   def __init__(self, icon_path, menu_items):
      super(TrayMenu, self).__init__()

      self._menu_items = menu_items
      self._icon = Gtk.StatusIcon() #Gtk.status_icon_new_from_file(icon_path)
      self._icon.set_from_file(icon_path)

      #self._icon.connect('activate', lambda *args: self._make_menu())
      #self._icon.connect('popup-menu', lambda *args: self._make_menu())
      self._icon.connect('button-press-event', lambda widget, event: self._make_menu(widget, event))


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


