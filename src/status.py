import logging, traceback
#import sys
logger = logging.getLogger(__name__)

def _err(s):
   globals()[s] = s

#something in this system isn't what we expect
_err('UNEXPECTEDSYS')
#we don't support this os
_err('UNSUPPORTEDOS')
#called stuff without initializing or called things in wrong order
_err('BADAPICALL')
#unknown status
_err('UNKNOWN')
#download exception
_err('DOWNLOAD')
#random stuff that doesn't go anywhere else
_err('OTHER')

class Error(Exception):
   #status is like error code
   def __init__(self, status, msg = ''):
      assert status == eval(status)
      self._msg = msg
      self.status = status
      logger.critical(self.__str__())

   def __str__(self):
      trace = traceback.format_exception(type(self), self, self.__traceback__)
      print_format = (self.status, repr(self._msg), trace)
      return 'Status: %s: %s... \n%s' % print_format

#TODO: removeme
#f = open('tmp/updater1', 'rw')
#traceback.print_exc(file=sys.stderr) #sys.stdout)
#f.close()
#store in variable = traceback.format_exc()

######USAGE
#import error
#from error import Error
#raise Error(error.UNKNOWN, 'error string')
