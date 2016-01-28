import tarfile
import io
import os
import os.path
import shutil
from pycloak.events import Event
from pycloak.shellutils import rm

class CustomFileObject(io.FileIO):
   def __init__(self, path, *args, **kwargs):
      self._file_size = os.path.getsize(path)
      self.on_read_progress = Event()
      super(CustomFileObject, self).__init__(path, *args, **kwargs)

   def read(self, size):
      self.on_read_progress((self.tell() * 100) / self._file_size, self._file_size, self.tell())
      return io.FileIO.read(self, size)

def untar(path, extract_path, on_progress):
   cfile = CustomFileObject(path)
   cfile.on_read_progress += on_progress
   with tarfile.open(fileobj=cfile, mode='r') as t:
      members = t.getmembers()
      total = len(members)
      count=0
      for member in members:
         count+=1
         t.extract(member, extract_path)
         #on_progress((count * 100) / total, total, count, member.name)

def untar2(path, extract_path, on_progress, delete_destination_paths = False):
   cfile = CustomFileObject(path)
   cfile.on_read_progress += on_progress
   with tarfile.open(fileobj=cfile, mode='r') as t:
      if delete_destination_paths:
         for(member in t.getnames()):
            full_path = os.path.join(extract_path, member)
            if os.path.exists(full_path):
               rm(full_path, False)

      t.extractall(extract_path)
