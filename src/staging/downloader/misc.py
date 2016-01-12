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


