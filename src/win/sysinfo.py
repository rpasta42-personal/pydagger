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

def becomeAdmin(exec_path, debug=False, wait=False, show_shell=True):
   if not isUserAdmin():
      path = sys.executable
      args = sys.argv

      cmd = '"%s"' % path
      params = " ".join(['"%s"' % (x,) for x in args])
      cmdDir = ''
      if show_shell:
         showCmd = win32con.SW_SHOWNORMAL
      else:
         showCmd = win32con.SW_HIDE

      procInfo = ShellExecuteEx(
         nShow=showCmd,
         fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
         lpVerb='runas',
         lpFile=cmd,
         lpParameters=params)

      if wait:
         procHandle = procInfo['hProcess']
         obj = win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
         rc = win32process.GetExitCodeProcess(procHandle)
      else:
         rc = None

      return True
   return False

      
   
