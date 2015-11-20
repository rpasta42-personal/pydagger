#!/usr/bin/env python

from pycloak.events import Event
from pycloak.threadutils import EzThread
import json, sys, time, threading

def console_log(msg):
   sys.stderr.write('got msg from python: %s\n' % string)
   sys.stderr.flush()

class ElectronTalker:
   def __init__(self, msg_handler = None):
      self._stop = False
      self.on_msg = Event()
      if msg_handler is not None:
         self.on_msg += msg_handler

      self.t = EzThread(self.reader_thread).thread

   def read_json(self):
      data = None
      try:
         line = sys.stdin.readline()
         if line:
            data = line.strip()
      except:
         pass
      return json.loads(data)

   def reader_thread(self):
      while not self._stop:
         time.sleep(0.05)
         msg = self.read_json()
         self.on_msg(msg)

   def send_json(self, data):
      data['magic'] = 'gentoo_sicp_rms'
      json_data = json.dumps(data)
      sys.stdout.write("%s\n" % json.dumps(data))
      sys.stdout.flush()

   def send_cmd(self, action, value):
      cmd = { 'action': action, 'value': value }
      self.send_json(cmd)

   def stop(self):
      self._stop = True


##############
url = 'https://icloak.me/kkave/50mb/test.update_info'

def get_version():
   return 0
def get_new_version():
   return 1

def show_section(e, section):
   e.send_cmd('show_section', section)

def progress_download(e, curr, total):
   #console_log(curr + ' ' + total)
   percent = curr/total * 100
   e.send_cmd('progress', percent)

def testProgress():
   e = ElectronTalker(lambda msg: console_log(msg))

   def update_progress():
      i = 0
      while i < 50:
         time.sleep(0.1)
         i = i+0.5
         #e.send_json({ 'action':'progress', 'value': i })
   ez = EzThread(update_progress)
   ez.t.join()
   e.t.join()
   

def real_update():
   import UpdateWriter
   e = ElectronTalker(lambda msg: console_log(msg))

   show_section(e, 'checking4updates')
   time.sleep(1)
   show_section(e, 'downloadingUpdate')

   def update():
      from downloader import downloader
      conf, raw_path, json_path = downloader.download(url, 'tmp', onProgress=lambda a,b:progress_download(e, a, b))

   #ez = EzThread(update)
   update()
   #time.sleep(1)
   e.t.join()
   #ez.thread.join()

if __name__ == '__main__':
   real_update()
