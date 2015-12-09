import sys
import os
import traceback
import types
import ctypes
import win32api
import win32con
import win32event
import win32process
from win32com.shell.shell import ShellExecuteEx
from win32com.shell import shellcon

def isUserAdmin():
   try:
      return ctypes.windll.shell32.IsUserAnAdmin()
   except:
      traceback.print_exc()
      return False

def becomeAdmin(exec_path, debug=False, wait=False):
   if not isUserAdmin():
      if hasattr(sys, 'frozen'):
         path = os.path.abspath(sys.executable)
         args = sys.argv
      else:
         path = sys.executable
         args = sys.argv

      cmd = '"%s"' % path
      params = " ".join(['"%s"' % (x,) for x in args])
      cmdDir = ''
      chowCmd = win32con.SW.SHOWNORMAL
      procInfo = ShellExecuteEx(
         nShow=showCmd,
         fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
         lbVerb='runas',
         lpFile=cmd,
         lpParams=params)

      if wait:
         procHandle = procInfo['hProcess']
         obj = win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
         rc = win32process.GetExitCodeProcess(procHandle)
      else:
         rc = None
   return rc

      
   
