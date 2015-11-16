#!/usr/bin/env python

import os, sys, time, argparse, json
from pycloak.IPC.stdio import StdioCom
from pycloak.events import Event

class Server(StdioCom):
   def __init__(self, namespace):
      super(Server, self).__init__(namespace)
      self.on_event = Event()

   def get_api_version(self):
      """Returns the service api version."""
      return "v0.1"
   get_api_version.exposed = True

   def call_me_back_brah(self):
      def ret(result):
         print(result)
      def print_msg(msg):
         print(msg)

      test = self.call('hi', ['Felipe', 'Orellana'])
      test['on_result'] += ret
      test['on_error'] += print_msg
      return 68
   call_me_back_brah.exposed = True

if __name__ == "__main__":
   srv = Server('testApi')
   if len(sys.argv) > 1:
      if sys.argv[1] == 'print':
         print(srv.generate_api('nodejs')) #or javascript or text or html
      elif sys.argv[1] == 'file':
         path = 'ui-pkg/node_modules/testapi.js' #sys.argv[2]
         f = open(path, 'w')
         f.write(srv.generate_api('nodejs'))

   else:
      import signal
      def _signal_handler(signal, frame):
         global srv
         srv.stop()

      signal.signal(signal.SIGINT, _signal_handler)
      signal.signal(signal.SIGTERM, _signal_handler)

      srv.start()

if 0:
   # argument parsing
   parser = argparse.ArgumentParser(description="One Ring keyring service")
   parser_sub = parser.add_subparsers(dest='mode', help="Developer tools for client applications")

   # main.py dev
   dev = parser_sub.add_parser('dev')
   dev_sub = dev.add_subparsers(dest="action")

   # main.py service --start -path=<store file path or store directory path>
   service = parser_sub.add_parser('service')
   service.add_argument('--start', '-s', dest="service", action="store_const", const="start")
   service.add_argument('--path', '-p', dest="path")

   # main.py dev generate
   generate = dev_sub.add_parser('generate', help="Documentation and API generator for client applications")
   generate_sub = generate.add_subparsers(dest='generate')

   # main.py dev generate api --javascript
   api = generate_sub.add_parser('api', help="API generator")
   api.add_argument('--javascript', dest="lang", action="store_const", const="javascript", help="Generates javascript bindings to communicate with server through stdio using jsonrpc protocol")
   api.add_argument('--nodejs', dest="lang", action="store_const", const="nodejs", help="Generates nodejs module bindings to communicate with server through stdio using jsonrpc protocol")

   # main.py dev generate doc [--text|--html]
   doc = generate_sub.add_parser('doc', help="Documentation generator")
   doc.add_argument('--text', dest="format", action="store_const", const="text", help="Simple text based documentation generator")
   doc.add_argument('--html', dest="format", action="store_const", const="html", help="Simple html based documentation generator")

   args = parser.parse_args()

   if "mode" not in args or args.mode == None:
      parser.print_help()
      sys.exit(1)

   if args.mode == "dev":
      if "action" not in args or args.action == None:
         parser.print_help()
         sys.exit(1)
      elif args.action == "generate":
         if args.generate == "api":
            srv = Server("onering")
            print(srv.generate_api(args.lang))
            sys.exit(0)
         elif args.generate == "doc":
            srv = Server("onering")
            print(srv.generate_doc(args.format))
            sys.exit(0)
         else:
            parser.print_help()
            sys.exit(1)
   elif args.mode == "service":
      if args.service == "start":
         import signal

         srv = Server("updater", args.path)
         def _signal_handler(signal, frame):
            global srv
            srv.stop()

         signal.signal(signal.SIGINT, _signal_handler)
         signal.signal(signal.SIGTERM, _signal_handler)
         srv.start()
      else:
         parser.print_help()

