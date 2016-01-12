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

local_remote_differ = 'Local and remote %s differ. Re-starting'

def same_dict(a, b):
   if cmp(a, b) == 0:
      return True
   else:
      return False

def get_latest_json(serv_url, download_dir, name):


def get_conf(url, download_dir):
   if not file_exists(download_dir):
      shellutils.mkdir(download_dir)

   conf_path   = join(download_dir, conf_fname)
   hashes_path = join(download_dir, hashes_fname)

   conf_url    = urljoin(url, conf_fname)
   hashes_url  = urljoin(url, hashes_fname)

   resuming    = True

   conf_serv = conf = None
   hashes_serv = hashes = None

   try:
      conf_serv = misc.json_from_url(url)
   except Exception e:
      var = traceback.format_exc()
      msg = "Can't get %s from %s. " % (conf_fname, conf_url)
      msg += "Got this error: %s" % var
      raise Error(error.DOWNLOAD, msg)

   conf = read_json(conf_path)
   if conf is None:
      msg =  'No local %s file found. ' % conf_fname
      msg += 'Downloading %s from server.' % conf_fname
      logger.info(msg)
      conf = conf_serv
      resuming = False
   else:
      logger.info('%s read successfully' % conf_fname)
      if same_dict(conf, conf_serv):
         logger.info('%s is latest. Resuming.' % conf_fname)
      else:
         logger.info(local_remote_differ % conf_fname)
         resuming = False
         conf = conf_serv

   hashes_serv = misc.json_from_url(hashes_url)
   hashes =  read_json(hashes_path)
   if not file_exists(hashes_path):
      logger.info('No local %s file found.' % hashes_fname)
      resuming = False
      hashes = hashes_serv
   else:
      logger.info('Local %s file found. Checking contents.' % hashes_fname)
      hashes = read_json(hashes_path)
      if same_dict(hashes, hashes_serv):
         logger.info('%s is latest.' % hashes_fname)
      else:
         logger.info(local_remote_differ % hashes_fname)
         resuming = False
         hashes = hashes_serv

   raw_f_name = conf['raw-file']
   raw_path = join(download_dir, raw_f_name)

   raw_url = '/'.join(url.split('/')[:-1]) + '/' + raw_f_name
   #bro_url = raw_url + '.brotli'
   logger.info('raw file url: %s' % raw_url)

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

