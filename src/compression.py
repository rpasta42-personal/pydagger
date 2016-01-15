import tarfile
import io
import os

def untar(path, extract_path, on_progress):
   with tarfile.open(path, 'r') as t:
      members = t.getmembers()
      total = len(members)
      count=0
      for member in members:
         count+=1
         t.extract(member, extract_path)
         on_progress((count * 100) / total, member.name)

