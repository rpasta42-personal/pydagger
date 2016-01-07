#!/usr/bin/env python

class Timer:
   def __enter__(self):
      self.start = time.clock()
      return self

   def __exit__(self, *args):
      self.end = time.clock()
      self.interval = self.end - self.start

if __file__ == 'main':
   try:
      with Timer() as t:
         conn = httplib.HTTPConnection('google.com')
         conn.request('GET', '/')
   finally:
      print('Request took %.03f sec.' % t.interval)
