#TODO KK: ugly hack
import sys
import os
sys.path.insert(0, __file__ + '/..')
import status
from status import Status

import logging, logging.config
import requests, sys

cacert = True #os.path.join(os.path.abspath(os.path.dirname(sys.executable)), 'cacert.pem')
logger = logging.getLogger(__name__)

def get(url):
   r = requests.get(url, verify=cacert)
   if r.status_code == 200:
      return r.text
   else:
      msg = 'Could not download text file %s.' % url
      raise Status(status.DOWNLOAD, msg)

def json_from_url(url):
   r = requests.get(url, verify=cacert)
   if r.status_code == 200:
      return r.json()
   else:
      msg = 'Could not download json file %s.' % url
      raise Status(status.DOWNLOAD, msg)

#TODO: use OrderedDict
#https://docs.python.org/2/library/collections.html#collections.OrderedDict
def get_chunk_index(lst_of_chunks, hash_to_get):
   i = 0
   for x in lst_of_chunks:
      if x[0] == hash_to_get:
         return i
      i = i+1
   return None

def set_chunk_status(lst, hash_to_set, status):
   i = get_chunk_index(lst, hash_to_set)
   lst[i] = (lst[i][0], status)
   #print(lst[i])



