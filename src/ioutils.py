import os
import time
import threading
import threadutils
from events import Event

class FSMonitor(object):

   def __init__(self, paths, msg_queue, delay=.1):
      self.delay = delay
      self.msg_queue = msg_queue
      self.paths = paths
      self.worker = None
      self.on_file_created = Event()
      self.on_file_changed = Event()
      self.on_file_deleted = Event()
      self.on_dir_created = Event()
      self.on_dir_changed = Event()
      self.on_dir_deleted = Event()

   def start(self):
      if self.worker is None:
         self.worker = FSMonitorWorker(self, self.paths, self.msg_queue, self.delay)
         self.worker.start()
      else:
         raise Exception("Monitor already startted!")

   def stop(self):
      if self.worker:
         self.worker.lqueue.invoke(self.worker.stop_monitor)
         self.worker.join()
         self.worker = None
   
class FSMonitorWorker(threading.Thread):

   def __init__(self, parent, paths, msg_queue, delay=.1):
      super(FSMonitorWorker, self).__init__()
      self.delay = delay
      self.parent = parent
      self.mqueue = msg_queue
      self.paths = paths
      self.lqueue = threadutils.MessageQueue()
      self.monitor = False
      self.filestates = {}

   def run(self):
      self.monitor = True
      self.check_fs(self.paths, False)  # initial file run to create map of changes
      while self.monitor:
         for path in self.paths:
            self.check_fs(self.paths)

         self.lqueue.process()
         time.sleep(self.delay)

   def stop_monitor(self):
      self.monitor = False

   def check_fs(self, path, with_events=True):
      # we are tracking files encountered on this run. As they are found, they are removed from the list
      # below, any files left would then signify that they were deleted and not part of the FS anylonger.
      existing_paths = self.filestates.keys()

      # Walk the provided path and make a map of every file encountered
      for root, dirs, files in os.walk(path, topdown=False):
         for name in dirs:
            full_path = os.path.join(root, name)
            dir_state = self.filestates.get(full_path, None)
            try:
               # in a try block in case file dissapears in the middle of scanning it
               mtime = os.path.getmtime(full_path)
            except:
               continue

            try:
               # lazy way of removing a path from the list without havin to find it first.
               existing_paths.remove(full_path)
            except ValueError:
               pass

            if dir_state is None:
               dir_state = {'mtime': mtime, 'root': root, 'name': name, 'is_dir': True}
               self.filestates[full_path] = dir_state
               if with_events:
                  self.mqueue.invoke(self.parent.on_dir_created, path=root, name=name, mtime=mtime)
            elif dir_state['mtime'] != mtime:
               dir_state['mtime'] = mtime
               if with_events:
                  self.mqueue.invoke(self.parent.on_dir_changed, path=root, name=name, mtime=mtime)

         for name in files:
            full_path = os.path.join(root, name)
            file_state = self.filestates.get(full_path, None)
            try:
               mtime = os.path.getmtime(full_path)
            except:
               continue

            try:
               existing_paths.remove(full_path)
            except ValueError:
               pass

            if file_state is None:
               file_state = {'mtime': mtime, 'root': root, 'name':name, 'is_dir': False} 
               self.filestates[full_path] = file_state
               if with_events:
                  self.mqueue.invoke(self.parent.on_file_created, path=root, name=name, mtime=mtime)
            elif file_state['mtime'] != mtime:
               file_state['mtime'] = mtime
               if with_events:
                  self.mqueue.invoke(self.parent.on_file_changed, path=root, name=name, mtime=mtime)


      for path in existing_paths:
         path_state = self.filestates.get(path, None)
         if path_state:
            if path_state["is_dir"]:
               if with_events:
                  self.mqueue.invoke(
                        self.parent.on_dir_deleted, 
                        path=path_state['root'], 
                        name=path_state['name'], 
                        mtime=time.time())
            else:
               if with_events:
                  self.mqueue.invoke(
                        self.parent.on_file_deleted, 
                        path=path_state['root'], 
                        name=path_state['name'], 
                        mtime=time.time())
            self.filestates.pop(path, None)
            
if __name__ == "__main__":

   import signal
   import sys
   import shutil

   demo_run = True
   queue = threadutils.MessageQueue()
   monitor = FSMonitor(sys.argv[1], queue)
   monitor.start()

   def signal_handler(signal, frame):
      global demo_run
      demo_run = False
      monitor.stop()
      sys.exit(0)

   signal.signal(signal.SIGINT, signal_handler)
   signal.signal(signal.SIGTERM, signal_handler)

   def on_file_created(path, name, mtime):
      print("FILE CREATED: %s %s %s" % (path,name,mtime))

   def on_file_changed(path, name, mtime):
      print("FILE CHANGED: %s %s %s" % (path,name,mtime))

   def on_file_deleted(path, name, mtime):
      print("FILE DELETED: %s %s %s" % (path,name,mtime))

   def on_dir_created(path, name, mtime):
      print("DIR CREATED: %s %s %s" % (path, name, mtime))

   def on_dir_changed(path, name, mtime):
      print("DIR CHANGED: %s %s %s" % (path, name, mtime))

   def on_dir_deleted(path, name, mtime):
      print("DIR DELETED: %s %s %s" % (path, name, mtime))
   
   monitor.on_file_changed += on_file_changed
   monitor.on_file_created += on_file_created
   monitor.on_file_deleted += on_file_deleted
   monitor.on_dir_changed += on_dir_changed
   monitor.on_dir_created += on_dir_created
   monitor.on_dir_deleted += on_dir_deleted

   try:
      counter=0
      while demo_run:
         time.sleep(.5)
         queue.process()
   finally:
      print("Stoping monitor")
      monitor.stop()


