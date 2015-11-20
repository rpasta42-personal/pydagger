#!/usr/bin/python3

import logging, logging.config
import argparse, download, download2

logger = logging.getLogger(__name__)

def get_update_url():
   parser = argparse.ArgumentParser()
   parser.add_argument('-u', '--update_url', metavar='url', help='URL of update json file')
   parser.add_argument('-t', '--use-threads', dest='use_threads', action='store_true', help='Test downloading with threads')
   parser.add_argument('-s', '--single-file', dest='single_file', action='store_true', help='Test single file downloading mode')

   args = parser.parse_args()

   if args.update_url is None:
      update_url = 'http://updatertest/fake-update.update_info'
      #update_url = 'https://icloak.org/kkave/unit_test.update_info'
   else:
      update_url = args.update_url
   return (update_url, args.use_threads, args.single_file)

update_url, use_threads, single_file = get_update_url()
logger.info('Update json path: %s' % update_url)
logger.info('Using threads: %s' % use_threads)
logger.info('Dowload into single file: %s' % single_file)

download_func = download.download
if single_file:
   download_func = download2.download

download_func(update_url, 'tmp-update', use_threads)


