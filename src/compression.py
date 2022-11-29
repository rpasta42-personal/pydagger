import tarfile
import io
import os
import os.path
import shutil
import logging
import platform

from pycloak.events import Event
from pycloak.shellutils import rm

logger = logging.getLogger(__name__)


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

def untar2(path, extract_path, on_progress, delete_destination_paths = False, delete_destination_ignore = []):
   cfile = CustomFileObject(path)
   cfile.on_read_progress += on_progress
   with tarfile.open(fileobj=cfile, mode='r') as t:
      if delete_destination_paths:
         for member in t.getnames():
            if platform.system() == 'Windows':
               member = member.replace('/', '\\')
            full_path = os.path.join(extract_path, member)
            if os.path.exists(full_path):
               if member not in delete_destination_ignore:
                  rm(full_path, True)

      def is_within_directory(directory, target):
          
          abs_directory = os.path.abspath(directory)
          abs_target = os.path.abspath(target)
      
          prefix = os.path.commonprefix([abs_directory, abs_target])
          
          return prefix == abs_directory
      
      def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
      
          for member in tar.getmembers():
              member_path = os.path.join(path, member.name)
              if not is_within_directory(path, member_path):
                  raise Exception("Attempted Path Traversal in Tar File")
      
          tar.extractall(path, members, numeric_owner=numeric_owner) 
          
      
      safe_extract(t, extract_path)
