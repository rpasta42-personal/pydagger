import shutil, os.path, signal, os, subprocess
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

#same as running "ps -e" from bash
#returns a list of processing where each process is a hash with pid, term, time and process name.
def gnu_ps_e():
   processes = []
   child = pexpect.spawn('ps -e', timeout=None)

   while True:
      child.expect(["(?P<pid>[0-9]+)\s+(?P<term>[^\s]+)\s+(?P<timeran>[0-9:]+)\s+(?P<pname>[^\r]*)", pexpect.EOF])
      #print(child.after)
      if child.match == pexpect.EOF:
         break
      data = child.match.groupdict()

      #next 2 lines will mess up ps
      #if not child.isalive():
      #   break

      #print(data)
      processes.append(data)
   return processes

#name or pid
def get_proc(search_by, critaria, processes=None):
   if not processes:
      processes = gnu_ps_e()

   assert logical_xor(search_by=='name', search_by=='pid')
   if search_by == 'name':
      for proc_line in processes:
         proc_line['pid'] = int(proc_line['pid'])
         if proc_line['pname'] == critaria:
            return proc_line
   if search_by == 'pid':
      for proc_line in processes:
         proc_line['pid'] = int(proc_line['pid'])
         if proc_line['pid'] == critaria:
            return proc_line
   return None

def kill_proc(proc, sig=signal.SIGINT):
   if not proc:
      return #raise Exception('trying to kill non-existing process')
   elif isinstance(proc, basestring):
      kill_proc(get_proc('name', proc), sig)
   elif isinstance(proc, (int, long)):
      os.kill(proc, sig)
   else:
      kill_proc(int(proc['pid']), sig)
      #raise Exception('bad proc type')

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

