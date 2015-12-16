import shutil, os.path, signal, os, subprocess, json, sys
from multiprocessing import Process

def mkdir(name):
   """recursively create dirs (like mkdir -p)"""
   #os.mkdir(name) #make one directory
   #exists_ok prevents errors when dir already exists
   os.makedirs(name, exist_ok=True)

def ls(path):
   return os.listdir(path)

def is_file(path):
   return os.path.isfile(path)

def is_dir(path):
   return os.path.isdir(path)

def is_link(path):
   return os.path.islink(path)

def is_mount_point(path):
   return os.path.ismount(path)

def rm(path):
   """Removes files and directories"""
   if is_dir(path):
      #os.removedirs(path) #only works for empty
      shutil.rmtree(path)
   elif is_file(path) or is_link(path):
      os.remove(path)
   else:
      raise Exception('Trying to remove unknown file type')

def cp(src, dst):
   shutil.copytree(src, dst)

#say you have app/src/main.py. To get path of project directory (app) from main.py
#you can use get_relative_path(__file__, '..')
def get_abs_path_relative_to(current_file, relative_path = ''):
   from os.path import abspath, dirname, realpath
   return abspath(dirname(realpath(current_file)) + relative_path)

def file_exists(filePath):
   return filePath and os.path.exists(filePath)

def check_paths(*paths):
   bad = []
   for p in paths:
      if file_exists(p) is False:
         bad.append(p)
   return bad

def write_file(filePath, data, binary=False):
   flags = 'w'
   if binary:
      flags = 'wb'
   with open(filePath, flags) as f:
      return f.write(data)

def read_file(filePath, nBytes=None, binary=False, createIfNeeded=False):
   if file_exists(filePath):
      flags = 'r'
      if binary:
         flags = 'rb'
      with open(filePath, flags) as f:
         if nBytes:
            return f.read(nBytes)
         else:
            return f.read()
   elif filePath and createIfNeeded:
      assert not nBytes
      file(filePath, 'w').close()
   return None

def write_json(path, json_data):
   write_file(path, json.dumps(json_data) + '\n')

def read_json(path):
   if path:
      data = read_file(path)
      if data:
         return json.loads(data)
   return None

def get_file_size(filename):
   "Get the file size by seeking end"
   fd = os.open(filename, os.O_RDONLY)
   try:
      return os.lseek(fd, 0, os.SEEK_END)
   finally:
      os.close(fd)
   return -1


def parse_mtab():
   mounts = []
   mtab_str = read_file('/etc/mtab').strip()
   entries = mtab_str.split('\n')
   for entry in entries:
      lst = entry.split(' ')
      #http://serverfault.com/questions/267609/how-to-understand-etc-mtabm
      item = {
         'mount-device'    : lst[0], #current device in /dev/sd*[n]
         'mount-point'     : lst[1], #where it's mounted
         'file-system'     : lst[2],
         'mount-options'   : lst[3],
         'dump-cmd'        : lst[4],
         'fsck-order-boot' : lst[5]
      }
      mounts.append(item)
   return mounts

#works for drives and partitions
def get_mount_point(drive):
   mounts = parse_mtab()
   for device in mounts:
      if device['mount-device'] == drive:
         return device['mount-point']
   return None

#new thread non-block
def func_thread(callback):
   p = Process(target=callback).start()

#non-blocking
def exec_prog(command):
   if type(command) is list:
      args = command
   else:
      args = command.split()
   p = Process(target=lambda:subprocess.call(args))
   p.start()

def exec_sudo(cmd):
   return exec_get_stdout('gksudo %s' % cmd)

#TODO: use arrays instead of map/dict?
def exec_prog_with_env(command, envBindings):
   args = command.split()
   my_env = os.environ.copy() #vs os.environ
   for name in envBindings:
      my_env[name] = envBindings[name]

   def subProc():
      #TODO: why shell == True???
      subprocess.Popen(args, env=my_env, shell=True)

   Process(target=subProc).start()

#blocking, returns output
def exec_get_stdout(command):
   args = command.split()
   task = subprocess.Popen(args, stdout=subprocess.PIPE)
   return task.communicate()

class ProgressBar(object):
    def __init__(self, max_width = 20):
        self.spinner = ['/', '-', '\\', '-']
        self.spinner_tick = 0
        self.max_width = max_width

    def update(self, p, label=""):
        self.spinner_tick += 1
        i = int((p * self.max_width) / 100)
        s = self.spinner[self.spinner_tick % len(self.spinner)]
        bar = "%s%s%s" % ("".join(['='] * i), s, "".join([' '] * (self.max_width - i - 1)))
        sys.stdout.write("\r[%s] %s" % (bar, label))
        sys.stdout.flush()


