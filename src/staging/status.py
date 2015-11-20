import logging
logger = logging.getLogger(__name__)

def _stat(s):
   globals()[s] = s

#no problems
_stat('SUCCESS')
#can't find ICLOAK stick or too many plugged in.
#Only allow 1 stick at a time to update.
_stat('NUMDRIVES')
#can't find second partition on ICLOAK stick
_stat('BADDRIVE')
#can't find update file where it's supposed to be
_stat('NOUPDATEFILE')
#something in this system isn't what we expect
_stat('UNEXPECTEDSYS')
#we don't support this os
_stat('UNSUPPORTEDOS')
#unknown status
_stat('UNKNOWN')
#download exception
_stat('DOWNLOAD')

class Status(Exception):
   def __init__(self, status, msg = ''):
      assert status == eval(status)
      self._msg = msg
      self.status = status
      #logger.critical(self)

   def __str__(self):
      s = (self.status, repr(self._msg))
      return 'KKStatus: %s: %s' % s

#class MyLogger:
#   #output='file', output='terminal', output='jsconsole'
#   def __init__(self, log_type, logger=None, logging_file=None):
#      self.log_type = log_type
#      if log_type == 'file':
#      elif output == 'terminal':
#      elif output == 'jsconsole':
#   def update_logger(self, logger):


######USAGE
#import status
#from status import Status
#raise Status(status.UNKNOWN, 'error string')
