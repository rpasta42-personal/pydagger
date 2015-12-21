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
      # on frozen app we should be able to get path from sys
      if hasattr(sys, 'frozen'):
         path = os.path.abspath(sys.executable)
      else:
         path = os.path.abspath(os.path.dirname(sys.argv[0])) + exec_path

      DISPLAY=os.environ['DISPLAY']
      XAUTHORITY=os.environ['XAUTHORITY']
      cmd = ["pkexec", "env", "DISPLAY=%s" % DISPLAY, "XAUTHORITY=%s" % XAUTHORITY, path]
      #p = Popen(cmd, stdin=None, stdout=PIPE, stderr=PIPE)
      p = Popen(cmd, stdin=None, stdout=None, stderr=None)
      #out,err=p.communicate()
      #code=p.wait()
      return True
   return False


