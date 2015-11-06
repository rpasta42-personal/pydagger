#!/usr/bin/env python

import os, sys, time, argparse, json
from pycloak.IPC.stdio import StdioCom
from pycloak.events import Event

class Server(StdioCom):
   def __init__(self, namespace):
      super(Server, self).__init__(namespace)
      self.on_some_event = Event() #kk

   #####################################################
   ## Helper methods

   def iter_next_entry(self, entry_iter, type_id):
      while True:
         entry = entry_iter()
         if entry == None:
            break
         elif entry.get_data_type() == type_id:
            return entry.to_json()
      return None

   def iter_reset_entry(self):
      return self.keyring.get_entries

   #####################################################
   ## Exposed methods
   def get_api_version(self):
      """Returns the service api version."""
      return "v0.1"
   get_api_version.exposed = True

#   def password(self):
#      """Returns an object prefilled with all fields pertaining to password entries"""
#      return """
#   var default_fields = %s;
#   for (var attrname in fields) { if (typeof fields[attrname] !== 'function') { default_fields[attrname] = fields[attrname];} }
#   return default_fields;""" % json.dumps(storage)
#   password.exposed_args = ['fields']
#   password.exposed_raw = True
#
#   def start_session(self, account, pub_key):
#      """Stars a session using the provided certificate to encrypt sensitive information."""
#      self.keyring = KeyStorage(os.path.join(self._store_path, account, "data.ring"))
#      return {"session": 1234, "pub_key": "kldswhjfkl;j4h3434fldkfjdsg013489f3"}
#   start_session.exposed = True
#
#   def save_note(self, entry):
#      """Stores a note object"""
#      return self.keyring.store_entry_dict(entry, storage.ENTRY_NOTE)
#   save_note.exposed = True
#
#   def shutdown(self):
#      """stops server"""
#      self.stop()
#   shutdown.exposed = True
#

if __name__ == "__main__":
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

