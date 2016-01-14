#TODO KK: ugly hack
#import sys
#sys.path.insert(0, __file__ + '/..')
#import status
#from status import Status
#import logging, os, requests, xxhash
#from downloader.misc import json_from_url
#from pycloak.threadutils import ThreadQueue
#from pycloak import shellutils
#from pycloak.shellutils import file_exists, exec_prog
import misc
from pycloak.shellutils import join, file_exists, read_json
from pycloak import shellutils

from urlparse import urljoin

logger = logging.getLogger(__name__)

#threadQueue = ThreadQueue()

hashes_fname = 'hashes.json'
conf_fname = 'download.json'

def same_dict(a, b):
   if cmp(a, b) == 0:
      return True
   else:
      return False

def get_latest_json(serv_url, download_dir, fname):
   json_path = join(download_dir, fname)
   json_url = urljoin(serv_url, fname)

   json_local = json_serv = None
   resuming = True

   try:
      json_serv = misc.json_from_url(json_url)
   except Exception e:
      var = traceback.format_exc()
      msg = "Can't get %s from %s. " % (fname, json_url)
      msg += "Got this error: %s" % var
      raise Error(error.DOWNLOAD, msg)

   json = read_json(json_path)
   if json is None:
      msg =  'No local %s file found. ' % fname
      msg += 'Downloading %s from server.' % fname
      logger.info(msg)
      json = json_serv
      resuming = False
   else:
      logger.info('Local %s found. Checking contents.' % fname)
      if same_dict(json, json_serv):
         logger.info('%s is latest.' % fname)
      else:
         logger.info('Local and remote %s differ.' % fname)
         resuming = False
         json = json_serv
   return json, resuming

def get_conf(serv_url, download_dir):
   if not file_exists(download_dir):
      shellutils.mkdir(download_dir)

   ret = get_latest_json(serv_url, download_dir, conf_fname)
   conf, latest_conf = ret
   ret = get_latest_json(serv_url, download_dir, hashes_fname)
   hashes, latest_hashes  = ret

   resuming = False
   if latest_conf and latest_hashes:
      resuming = True
      logger.info('Everything is up to date. Resuming.')
   else:
      logger.info('Files outdated. Restarting.')

   raw_f_name = conf['raw-file']
   raw_path = join(download_dir, raw_f_name)

   raw_url = urljoin(serv_url, raw_f_name)
   logger.info('raw file url: %s' % raw_url)

   #todo: left here
   return conf, raw_path, json_path, data_path, hashes_path, hashes, resuming, threadQueue, raw_url

bad_block = None

#TODO: need a way to handle errors without exceptions
def write_block_(data, hashes, final_file, offset, conf, progress, conf_path):
   chunk_hash = xxhash.xxh64(data).intdigest()
   good_hash = hashes[progress]

   if chunk_hash != good_hash:
      bad_block = good_hash
      logger.critical('Bad block')
      return

   final_file.seek(offset)
   final_file.write(data)
   #final_file.flush()
   conf['progress'] = progress+1
   with perftools.Timer(): #kk left here
      pass
   shellutils.write_json(conf_path, conf)

#single file version
def download(json_url, download_dir, onProgress, useThreads=False): #onComplete?
   conf, raw_path, json_path, data_path, hashes_path, hashes, resuming, threadQueue, raw_url = get_conf(json_url, download_dir, useThreads)

   write_block = write_block_
   if threadQueue is not None:
      write_block = lambda *args: threadQueue.add_task(write_block_, *args)

   if not resuming:
      shellutils.write_json(json_path, conf)
      hashes = json_from_url(json_url + '.hashes')
      shellutils.write_json(hashes_path, hashes)
      if file_exists(raw_path):
         shellutils.rm(raw_path)
   else:
      hashes = shellutils.read_json(hashes_path)

   progress = conf['progress']
   num_hashes = conf['num-hashes']
   blk_size = conf['block-size']

   final_file = open(raw_path, 'ab')
   while progress < num_hashes:
      if bad_block is not None:
         msg = 'Bad hash of download chunk %s' % bad_block
         logger.critical(msg)
         raise Status(status.DOWNLOAD, msg)

      offset = progress * blk_size
      end = offset + blk_size - 1

      header = { 'Range': 'bytes=%d-%d' % (offset, end) }
      #Stream=False makes it faster
      r = requests.get(raw_url, headers=header, stream=False, verify=True, allow_redirects=True)

      if r.status_code != 206:
         msg = 'Wrong code for getting chunk. Got %i' % r.status_code
         raise Status(status.DOWNLOAD, msg)
      data = r.content
      r.close()
      write_block(data, hashes, final_file, offset, conf, progress, json_path)
      progress = progress + 1
      onProgress(progress, num_hashes)

   if threadQueue is not None:
      logger.info('Waiting on writer threads')
      threadQueue.join()
      logger.info('Writer threads are done')

   #final_file.flush()
   final_file.close()

   if bad_block is None:
      logger.info('Download done!')
      return conf, raw_path, json_path
   else:
      msg = 'Have bad block %s' % bad_block
      logger.info(msg)
      raise Status(status.DOWNLOAD, msg)

