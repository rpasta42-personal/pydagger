
#First get a list of files you want to trace:
dbug_files = dbug.list_files("./", ".py", True) + dbug.list_files('/usr/lib/python2.7/dist-packages/dbus', ".py", True))
#Then run your code inside a with statement:

with dbug.Tracer(dbug_fiels) as t:
   #Your code here …

