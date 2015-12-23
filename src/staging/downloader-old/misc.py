#TODO KK: ugly hack
import sys
sys.path.insert(0, __file__ + '/..')
import status
from status import Status

import logging, logging.config
import requests, sys

logger = logging.getLogger(__name__)

def json_from_url(url):
   r = requests.get(url, verify=True)
   if r.status_code == 200:
      return r.json()
   else:
      msg = 'Could not download json file %s.' % url
      logger.critical(msg)
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



