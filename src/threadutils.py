import os
import time
import threading
import traceback
import inspect
import logging

LOGGER = logging.getLogger(__name__)

try:
   from queue import Queue
except:
   from Queue import Queue
from pycloak.events import Event

class MsgInvoke(object):
   """A method or function invocation message. Takes a callback and arguments which is later used
   during MessageQueue processing to call methods or functions in a thread"""

   def __init__(self, callback, args, kwargs):
      self.invoke = callback
      self.args = args
      self.kwargs = kwargs

   def process(self, queue):
      self.invoke(*self.args, **self.kwargs)


class MsgInvokeDelayed(MsgInvoke):
   """A delayed method or function invocation message. Takes a callback, a delay value and arguments which
   is later used during MessageQueue processing to call methods or functions in a thread"""

   def __init__(self, callback, delay, args, kwargs):
      self.created = time.time()
      self.delay = delay
      super(MsgInvokeDelayed, self).__init__(callback, args, kwargs)

   def process(self, queue):
      if time.time() >= self.created + self.delay:
         super(MsgInvokeDelayed, self).process(queue)
      else:
         # not time to invoke yet, put msg back into queue
         queue.enqueue(self)

class MessageQueue(object):
   """A generic thread safe extensible message queue. Can be used to invoke methods between threads, or
   passing custom messages and processing. See MsgInvoke and MsgInvokeDelayed classes for extensibility
   implementation examples."""

   def __init__(self):
      self.processing = False
      self.__queue__ = Queue()
      self.__delayed__queue = Queue()
      self.__lock__ = threading.Lock()

   def empty(self):
      """Returns True if message queue is empty"""
      return self.__queue__.empty()

   def enqueue(self, msg):
      """enqueues a message for later processing"""
      with self.__lock__:
         if not self.processing:
            self.__queue__.put(msg)
         else:
            self.__delayed__queue.put(msg)

   def dequeue(self):
      """Removes a message from the queue"""
      with self.__lock__:
         return self.__queue__.get()

   def process(self):
      """Processes all queued messages in the current thread context"""
      self.processing = True
      while not self.empty():
         msg = self.dequeue()
         try:
            msg.process(self)
         except:
            print(traceback.format_exc())
      self.processing = False

      # queue any msgs added while processing was running
      while not self.__delayed__queue.empty():
         self.enqueue(self.__delayed__queue.get())

   def invoke(self, callback, *args, **kwargs):
      """Built in helper method to add a method or function invocation message"""
      self.enqueue(MsgInvoke(callback, args, kwargs))

   def invokeDelayed(self, callback, delay, *args, **kwargs):
      """Built in helper method to add a delayed method or function invocation message"""
      self.enqueue(MsgInvokeDelayed(callback, delay, args, kwargs))

class EzThread:
   def __init__(self, func, args=None, on_finish=None):
      self.done = False

      self.on_finish = Event()
      if on_finish is not None:
         self.on_finish += on_finish

      def call():
         if args == None:
            on_finish(func())
         else:
            on_finish(func(*args))
         self.done = True
      self.thread = self.t = threading.Thread(target=call)
      self.t.daemon = True
      self.t.start()

class Worker(threading.Thread):
   """Generic enhanced thread class. Uses MessageQueue to pass
   messages back and forth from parent thread to this thread"""

   def __init__(self, worker_fn, parent_message_queue=None, use_message_queue=True):
      super(Worker, self).__init__()
      assert worker_fn is not None, "worker_fn can NOT be None."
      
      self.parent_thread = parent_message_queue
      self.worker = worker_fn
      if use_message_queue:
         self.worker_thread = MessageQueue()
      else:
         self.worker_thread = None
      self.is_running = False
      self.on_exit = Event()
      self.on_error = Event()
      self.daemon = True
      self.paused = False

   def stop(self):
      self.is_running = False

   def pause(self, p):
      self.paused = p

   def run(self):
      self.is_running = True

      if inspect.isgeneratorfunction(self.worker):
         LOGGER.info("Worker is a generator")
         try:
            for i in self.worker(self):
               if self.paused:
                  while self.paused and self.is_running:
                     if self.worker_thread:
                        self.worker_thread.process()
               else:
                  if self.worker_thread:
                     self.worker_thread.process()
         except:
            LOGGER.info(traceback.format_exc())
            self.on_error(traceback.format_exc())
      else:
         LOGGER.info("Worker is not a generator")
         try:
            self.worker(self)
         except:
            LOGGER.info(traceback.format_exc())
            self.on_error(traceback.format_exc())

      self.is_running = False
      if self.parent_thread != None:
         self.parent_thread.invoke(self.on_exit, self)

class ThreadQueue():
   #def __init__(...., busy_sleep = 0.05)??
   def __init__(self, num_workers=1):
      self.q = Queue()
      self.lock = threading.Lock()
      #self.busy_sleep = busy_sleep

      for i in range(0, num_workers):
         t = threading.Thread(target=self._worker)
         t.daemon = True
         t.start()

   def join(self):
      self.q.join()

   def _worker(self):
      while True:
         item = self.q.get(block=True)
         f, callback, args, kwargs = item
         callback(f(*args, **kwargs))
         self.q.task_done()
         #time.sleep(self.busy_sleep)

   def add_task_callback(self, f, callback, *args, **kwargs):
      self.q.put([f, callback, args, kwargs])

   def add_task(self, f, *args, **kwargs):
      def fake_callback(*args, **kwargs):
         pass
      self.add_task_callback(f, fake_callback, *args, **kwargs)


if __name__ == "__main__":
   def test_workers():
      threadQueue = ThreadQueue(10)

      def work(n):
         time.sleep(0.5)
         with threadQueue.lock:
            print('thread msg: %i\n' % n)
         return 0

      def callback(x):
         print('task returned %i' % x)

      for i in range(0, 15):
         threadQueue.add_task_callback(work, callback, i)
      threadQueue.join()
      print('main thread')

   test_workers()

#testing my stuff so temporarily disable Felipe's test
if 1 == 0:
   # This is a simple example of how the MessageQueue would be used between two threads
   class threadtest(threading.Thread):
      def __init__(self, mqueue):
         super(threadtest, self).__init__()
         self.mqueue = mqueue
         self.count = 0
         self.lqueue = MessageQueue()
         self.alive=True

      def run(self):
         while self.alive:
            self.mqueue.invoke(test, "ON THREAD %s" % self.count)
            self.count+=1
            time.sleep(.5)
            self.lqueue.process()

      def die(self):
         print("Thread now dying!")
         self.alive=False

   def test(t):
      print("Hi!: %s" % t)

   mqueue = MessageQueue()
   t = threadtest(mqueue)
   counter=0
   t.setDaemon(True)
   t.start()
   mqueue.invokeDelayed(test, 2, "Delayed!")
   while True:
      mqueue.invoke(test, counter)
      counter+=1
      time.sleep(1)
      mqueue.process()
      if counter == 10:
         t.lqueue.invoke(t.die)
         t.join()
         print("Exiting...")
         break

#EzThread example
if False:
   from pycloak.threadutils import EzThread
   import time, threading

   l = threading.Lock()

   def worker(a, b):
       i = 0
       while i < 10:
           i = i+1
           with l:
               print("%i %s %s" % (i, a, b))
           time.sleep(0.5)
       return 5

   def blah(x):
       print(x)

   b = EzThread(worker, ["hello", "world"], blah)

   #while b.done is not True:
   #    time.sleep(1)
   b.thread.join()
