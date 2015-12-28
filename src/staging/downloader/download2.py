#TODO KK: ugly hack
import sys
sys.path.insert(0, __file__ + '/..')
import status
from status import Status
import logging, os, requests, xxhash
from downloader.misc import json_from_url
from pycloak.threadutils import ThreadQueue
from pycloak import shellutils
from pycloak.shellutils import file_exists, exec_prog

cacert = True #os.path.join(os.path.abspath(os.path.dirname(sys.executable)), 'cacert.pem')
logger = logging.getLogger(__name__)

def get_conf(url, download_dir, useThreads):
   data_path   = download_dir + '/download_data'
   json_path   = download_dir + '/download.json'
   hashes_path = download_dir + '/hashes.json'
   hashes      = None
   resuming    = True

   threadQueue = None
   if useThreads:
      threadQueue = ThreadQueue()

   if not file_exists(download_dir):
      os.mkdir(download_dir)

   conf_new = json_from_url(url)
   conf = shellutils.read_json(json_path)
   if conf is None:
      logger.info('No local download.json file found. Downloading download.json from server.')
      conf = conf_new
      resuming = False
   else:
      logger.info('download.json read successfully')

   if not file_exists(hashes_path):
      logger.info('No local hashes.json file found.')
      resuming = False
   else:
      logger.info('Local hashes file found.')

   new_conf_ver = int(conf_new['version'])
   conf_ver = int(conf['version'])
   if new_conf_ver > conf_ver or new_conf_ver == -1:
      conf = conf_new
      logger.info('download.json on server is newer than local version. Restarting download process.')
      resuming = False
   else:
      logger.info('Local download.json is the newest version.')
   #have good conf now

   raw_f_name = conf['raw-file']
   raw_path = download_dir + '/' + raw_f_name
   raw_url = '/'.join(url.split('/')[:-1]) + '/' + raw_f_name
   #bro_url = raw_url + '.brotli'
   logger.info('raw file url: %s' % raw_url)

   #compress = int(conf['compression'])
   #if compress != 0 and compress != 1:
   #   logger.critical('Unsupported compression type: %i.' % compress)
   #if compress == 1:
   #   import brotli
   #   url_to_download = bro_url

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
      r = requests.get(raw_url, headers=header, stream=False, verify=cacert, allow_redirects=True)

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

