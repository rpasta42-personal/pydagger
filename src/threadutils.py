import os, time, threading
from queue import Queue

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
      self.__delayed__queue = Queue.Queue()
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
         msg.process(self)
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


class ThreadQueue():
   def __init__(self):
      self.q = Queue()
      self.lock = threading.Lock()
      t = threading.Thread(target=self._worker)
      #?? t.daemon = False
      t.daemon = True
      t.start()

   def join(self):
      self.q.join()

   def _worker(self):
      while True:
         time.sleep(0.05)
         item = self.q.get(block=True)
         f, callback, args, kwargs = item
         callback(f(*args, **kwargs))
         self.q.task_done()

   def add_task_callback(self, f, callback, *args, **kwargs):
      self.q.put([f, callback, args, kwargs])

   def add_task(self, f, *args, **kwargs):
      def fake_callback(*args, **kwargs):
         pass
      self.add_task_callback(f, fake_callback, *args, **kwargs)

if __name__ == "__main__":
   threadQueue = ThreadQueue()

   def f(n):
      with threadQueue.lock:
         print('thread msg: %i\n' % n)
      return 0
   def callback(x):
      print('task returned %i' % x)

   threadQueue.add_task_callback(f, callback, 4)
   #threadQueue.add_task(f, callback, 4)

   print('main thread')
   time.sleep(1)
   threadQueue.join()

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


