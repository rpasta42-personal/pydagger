import os
import sys
import plistlib
import shutil
import subprocess
from subprocess import Popen, PIPE
import logging

logger = logging.getLogger(__name__)

def becomeAdmin(exec_path, debug=False):
   try:
      logger.info("=== Testing if user is root")
      os.setuid(0)
      logger.info(" == User is root")
      return True
   except Exception as e:
      logger.info(" == User is NOT root")
      # on frozen app we should be able to get path from sys
      if hasattr(sys, 'frozen'):
         path = os.path.abspath(sys.executable)
      else:
         path = os.path.abspath(os.path.dirname(sys.argv[0])) + exec_path

      logger.info("  = Attempting to relaunch through pkexec")
      DISPLAY=os.environ['DISPLAY']
      XAUTHORITY=os.environ['XAUTHORITY']
      cmd = ["pkexec", "env", "DISPLAY=%s" % DISPLAY, "XAUTHORITY=%s" % XAUTHORITY, path]
      logger.info("  = %s" % cmd)
      #p = Popen(cmd, stdin=None, stdout=PIPE, stderr=PIPE)
      p = Popen(cmd, stdin=None, stdout=None, stderr=None)
      #out,err=p.communicate()
      #code=p.wait()
      return True
   return False


