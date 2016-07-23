#!/usr/bin/env python

import sh
from pycloak import shellutils as psu

path = "."

#path, filename, size, perm checksum
def get_checksums(path):
   pass

#file, directory size and permissions
def rec_dir(path):
   childs = sh.ls().split()
   for child in childs:
      if psu.is_dir(path + childs[i]):
         rec_dir(path + childs[i])
