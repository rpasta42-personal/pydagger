import os
import sys
import plistlib
import shutil
import subprocess
from subprocess import Popen, PIPE

def findMountPoint(path):
	p1 = Popen(['diskutil', 'info', path], stdout=PIPE)
	(output, err) = p1.communicate()
	if output is not None:
		output = output.decode('utf8')
	if err is not None:
		err = err.decode('utf8')
	exit_code = p1.wait()

	result = dict()
	for line in output.splitlines():
		line = line.strip()
		if len(line) > 0:
			key, value = line.split(":")
			key = key.strip()
			value = value.strip()
			result[key] = value

	if exit_code == 0:
		return (True, result)

	return (False, '')

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

      path = path.replace(' ', '\\\\ ') # ensuring to escape spaces for apple script syntax
      applescript = 'do shell script "%s"  '\
         'with administrator privileges' % path

      if debug:
         print(applescript)

      p = Popen(["osascript", "-e", applescript], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      if debug:
         for line in p.stdout:
            sys.stdout.write(line.decode('utf8'))
         p.wait()

      return True
   return False


