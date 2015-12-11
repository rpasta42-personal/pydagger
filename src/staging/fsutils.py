import platform

#Linux & OS X version
def _fsck_msdos(path):
   # fix file systems
   plat = platform.system()
   fsck_cmd = None
   if plat == 'Linux':
        fsck_cmd = ["fsck.msdos", "-fy", path]
   elif plat == 'Darwin':
      fsck_cmd = ["fsck_msdos", "-fy", path]
   else:
      raise Status(status.UNSUPPORTEDOS, 'fsck_msdos is only available on Linux and OS X')

   process = Popen(fsck_cmd, stdout=PIPE)
   (output, err) = process.communicate()
   exit_code = process.wait()
   print("=== fsck %s" % path)
   print(output)
   print(err)
   if exit_code == 0:
      return (True, '')
   return (False, err)

#
