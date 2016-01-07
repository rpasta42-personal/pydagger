#!/usr/bin/env python
import time, requests #httplib

class Timer:
   def __enter__(self):
      self.start = time.clock()
      return self

   def __exit__(self, *args):
      self.end = time.clock()
      self.interval = self.end - self.start
      #print('Time: %.03f' % self.interval)

if __name__ == '__main__':
   try:
      with Timer() as t:
         #conn = httplib.HTTPConnection('google.com')
         #conn.request('GET', '/')
         requests.get('https://google.com')
      print('Request took %.03f sec.' % t.interval)
   finally:
      print('Request took %.03f sec.' % t.interval)
