import os
import os.path
import sys
import inspect
from termcolor import colored, cprint

halt_flags = dict()

def halt_on(key, value, label, fn):
	global halt_flags
	if key not in halt_flags:
		halt_flags[key] = list()

	if fn(halt_flags[key], value):
		print(label % (halt_flags[key], value))
		sys.exit(1)

	halt_flags[key].append(value)

class ConsoleInfo(object):

	def __init__(self):
		rows, columns = os.popen('stty size', 'r').read().split()
		self.rows = int(rows)
		self.columns = int(columns)

def list_dirs(path, recursive=True):
	path = os.path.abspath(path)
	res = list()
	for p in os.listdir(path):
		if os.path.isdir("%s/%s" % (path, p)):
			res.append("%s/%s" % (path,p))
			if recursive:
				res.extend(list_dirs("%s/%s" % (path, p)))
	return res

def list_files(path, ext=None, recursive=True):
	path = os.path.abspath(path)
	res = list()
	for p in os.listdir(path):
		if not os.path.isdir("%s/%s" % (path, p)):
			filename, p_ext = os.path.splitext(p)
			if ext == None:
				res.append("%s/%s" % (path,p))
			elif p_ext == ext:
				res.append("%s/%s" % (path,p))
				
		elif recursive:
			res.extend(list_files("%s/%s" % (path, p), ext, recursive))
	return res

class Tracer(object):

	def __init__(self, file_watch_list = None):
		self.file_watch_list = file_watch_list
		self.console = ConsoleInfo()
		self.last_file = None

	def trace(self, frame, event, arg):
		filename = frame.f_code.co_filename
		name = frame.f_code.co_name
		lineno = frame.f_lineno
		out = None
		traceme = False
		log = ""
		ret = None
		linecol = 'yellow'
		filecol = 'red'

		if self.file_watch_list:
			if filename in self.file_watch_list:
				traceme = True
		else:
			traceme = True
		
		if event == "call":
			f_args, _, _, value_dict = inspect.getargvalues(frame)
			cls = None
			try:
				if len(f_args) and f_args[0] == 'self':
					instance = value_dict.get('self', None)
					if instance != None:
						cls = getattr(instance, '__class__', None)
			except:
				pass
			vals = []
			for k,v in value_dict.items():
				try:
					vals.append("%s=%s" % (k, str(v)))
				except:
					vals.append("%s=[UNKNOWN]" % k)
					pass
			if cls:
				log = "%s.%s (%s)" % (cls, name, ', '.join(vals))
			else:
				log = "%s (%s)" % (name, ', '.join(vals))
			ret = self.trace
		elif event == "line":
			log = "..."
		elif event == "return":
			try:
				str_arg = str(arg)
			except:
				str_arg = "UNKNOWN TYPE"
			log = "RETURN %s" % colored(str_arg, 'white')
			linecol = 'magenta'
		elif event == "exception":
			exc_type, exc_value, exc_traceback = arg
			log = "%s%s \"%s\" on line %s of %s" % (
				colored("[EXCEPTION] ", 'red', attrs=['blink', 'bold']),
				exc_type.__name__, 
				exc_value, 
				lineno, colored(name, 'cyan'))
		else:
			return
			
		if traceme:
			f = frame.f_back
			i=0
			while f:
				i += 1
				f = f.f_back

			extra = ""
			tab = "|" * i
			info = "%s%s %s" % (tab, colored("[%s]"%lineno, linecol), log)

			if self.last_file != filename:
				extra = " %s%s" % (
					" " * (self.console.columns - 1 - len(filename) - i),
					filename)
				extra = colored(extra, filecol, 'on_white', attrs=['underline', 'bold'])
				print("%s%s" % (tab,extra))
			print(info)
			self.last_file = filename

		if ret:
			return ret

		return

	def start(self):
		sys.settrace(self.trace)
	
	def stop(self):
		sys.settrace(None)

	def __enter__(self):
		self.start()
		return self
	
	def __exit__(self, type, value, traceback):
		self.stop()
