from pycloak.events import Event

import logging
logger = logging.getLogger(__name__)

class DeferredProgress(object):

   def __init__(self):
      self.on_progress = Event()
      self.fn = list()
      super(DeferredProgress, self).__init__()

   def add(self, fn, args=(), kwargs=dict(), label=None, ignore_errors=False):
      self.fn.append((fn, args, kwargs, label, ignore_errors)) # storing function argument and kw arguments as tuple here

   def exec(self):
      total_work = len(self.fn)
      count = 0
      for fn, args, kwargs, label, ignore_errors in self.fn:
         try:
            logging.info("Deferred: %s" % label)
            fn(*args, **kwargs)
         except Exception as e:
            logging.error(e)
            if not ignore_errors:
               raise e

         self.on_progress((count * 100 / total_work), total_work, count, label)
         count += 1
