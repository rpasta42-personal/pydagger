
class Timer:
   def __enter__(self):
      self.start = time.clock()
      return self

   def __exit__(self, *args):
      self.end = time.clock()
      self.interval = self.end - self.start

if __name__ == 'main':
   with Timer() as t:
      conn = httplib.HTTPConnection('google.com')
      conn.request('GET', '/')

print('Request took %.03f sec.' % t.interval)
