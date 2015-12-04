import shutil, os.path, signal, os, subprocess, json
from multiprocessing import Process

def mkdir(name):
   os.mkdir(name)

def ls(path):
   return os.listdir(path)

def rm(path):
   shutil.rmtree(path)

def cp(src, dst):
   shutil.copytree(src, dst)

#say you have app/src/main.py. To get path of project directory (app) from main.py
#you can use get_relative_path(__file__, '..')
def get_abs_path_relative_to(current_file, relative_path = ''):
   from os.path import abspath, dirname, realpath
   return abspath(dirname(realpath(current_file)) + relative_path)

def file_exists(filePath):
   return filePath and os.path.exists(filePath)

def write_file(filePath, data):
   with open(filePath, 'w') as f:
      return f.write(data)

def read_file(filePath, nBytes=None, createIfNeeded=False):
   if file_exists(filePath):
      with open(filePath, 'r') as f:
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

def parse_mtab():
   mounts = []
   mtab_str = read_file('/etc/mtab').strip()
   entries = mtab_str.split('\n')
   for entry in entries:
      lst = entry.split(' ')
      #http://serverfault.com/questions/267609/how-to-understand-etc-mtabm
      item = {
         'mount-device'    : lst[0],
         'mount-point'     : lst[1],
         'file-system'     : lst[2],
         'mount-options'   : lst[3],
         'dump-cmd'        : lst[4],
         'fsck-order-boot' : lst[5]
      }
      mounts.append(item)
   return mounts

#new thread non-block
def new_proc(callback):
   p = Process(target=callback).start()

#non-blocking
def exec_prog(command):
   if type(command) is list:
      args = command
   else:
      args = command.split()
   p = Process(target=lambda:subprocess.call(args))
   p.start()

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



