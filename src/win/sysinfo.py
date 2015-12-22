import sys
import os
import traceback
import types
import ctypes

def isUserAdmin():
   try:
      return ctypes.windll.shell32.IsUserAnAdmin()
   except:
      traceback.print_exc()
      return False

def becomeAdmin(exec_path, debug=False, wait=False, show_shell=True):
   if not isUserAdmin():
      path = sys.executable
      args = sys.argv

      cmd = '"%s"' % path
      params = " ".join(['"%s"' % (x,) for x in args])
      cmdDir = ''


      if show_shell:
         showCmd = 1
      else:
         showCmd = 0

      ctypes.windll.shell32.ShellExecuteW(None, 'runas', cmd,  params, None, showCmd)

      return True
   return False

      
   
