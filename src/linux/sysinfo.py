import os
import sys
import plistlib
import shutil
import subprocess
from subprocess import Popen, PIPE

def becomeAdmin(exec_path, debug=False):
   try:
      os.setuid(0)
   except Exception as e:
      # if not admins prompt for admin password
      # original path was: "/../MacOS/ICLOAK Standalone Updater " + VERSION[0].upper() + VERSION[1:len(VERSION)]
      # on frozen app we should be able to get path from sys
      if hasattr(sys, 'frozen'):
         path = os.path.abspath(sys.executable)
      else:
         path = os.path.abspath(os.path.dirname(sys.argv[0])) + exec_path
         DISPLAY=os.environ['DISPLAY']
         XAUTHORITY=os.environ['XAUTHORITY']
      p = Popen(["tkexec", "env", "DISPLAY=%s" % DISPLAY, "XAUTHORITY=%s" % XAUTHORITY, path], stdin=None, stdout=None, stderr=None)
      return True
   return False


