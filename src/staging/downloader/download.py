import os, os.path, logging
import requests, sys, shutil, glob, xxhash
from pycloak.threadutils import ThreadQueue
from downloader.download2 import get_conf
from pycloak.misc import write_conf, read_conf
from pycloak.shellutils import file_exists, exec_prog
from downloader.misc import json_from_url, get_chunk_index, set_chunk_status

logger = logging.getLogger(__name__)

def check_data(data_path, hashes):
   chunk_status = []
   for x in hashes:
      chunk_status.append((x, False))
   num_good = 0

   downloaded_chunks = glob.glob(data_path + '/*')
   for chunk_path in downloaded_chunks:
      chunk = None
      with open(chunk_path, 'rb') as chunk_file:
         chunk = chunk_file.read()
      try:
         good_hash = int(os.path.basename(chunk_path))
      except Exception as exception:
         logger.critical('Bad file name in tmp-data (not hash)')
         continue
      if get_chunk_i(chunk_status, good_hash) is None:
         logger.warning('Extra file found in update_data: %s.' % good_hash)
         continue
      current_hash = xxhash.xxh64(chunk).intdigest()
      if int(good_hash) != current_hash:
         logger.warning('Removing bad chunk: %s' % chunk_path)
         os.remove(chunk_path)
         continue

      set_chunk_status(chunk_status, good_hash, True)
      logger.info('Found good block: %s' % chunk_path)
      num_good += 1
   return chunk_status, num_good

def check_and_write_chunk(hashes, good_hash, data, data_path, threadQueue):
   #logger.info('writing %s' % name)
   data_hash = xxhash.xxh64(data).intdigest()
   if good_hash != data_hash:
      logger.critical('Bad hash of downloaded chunk %s.' % good_hash)
      return None

   def write_block():
      with open(data_path + '/' + str(good_hash), 'wb') as chunk_file:
         chunk_file.write(data)

   if threadQueue is None:
         write_block()
   else:
      threadQueue.add_task(write_block)
   return good_hash

def download(url, download_dir, onProgress, useThreads=False):
   conf, raw_path, json_path, data_path, hashes_path, hashes, resuming, threadQueue, url_to_download = get_conf(url, download_dir, useThreads)

   if not resuming:
      if file_exists(data_path):
         shutil.rmtree(data_path)
      os.mkdir(data_path)
      write_conf(json_path, conf)
      hashes = json_from_url(url + '.hashes')
      write_conf(hashes_path, hashes)
   else:
      hashes = read_conf(hashes_path)

   chunk_status, progress_tracker = check_data(data_path, hashes)
   block_size = conf['block-size']
   num_hashes = conf['num-hashes']
   download_done = False

   while not download_done:
      for x in chunk_status:
         if x[1] is True:
            continue

         start = block_size * get_chunk_index(chunk_status, x[0])
         end = start + block_size - 1
         resume_header = { 'Range': 'bytes=%d-%d' % (start, end) }
         r = requests.get(url_to_download, headers=resume_header, stream=True, verify=True, allow_redirects=True)

         if r.status_code != 206:
            err = 'Could not find update file on server'
            logger.critical(err)
            raise Exception(err)

         data = b''
         for c in r.iter_content(block_size):
            data += c

         #if compress == 1:
         #   data = brotli.decompress(data)
         chunk_hash = check_and_write_chunk(hashes, x[0], data, data_path, threadQueue)
         if chunk_hash is not None:
            set_chunk_status(chunk_status, chunk_hash, True)
            onProgress(progress_tracker, num_hashes)
            progress_tracker = progress_tracker + 1
         r.close()

      download_done = True
      for x in chunk_status: #chunk_status.items()
         if x[1] is False:
            download_done = False


   logger.info('Download done! Now putting stuff together')
   if threadQueue is not None:
      threadQueue.join()
   with open(raw_path, 'wb') as final_file:
      for x in hashes:
         with open(data_path + '/' + str(x), 'rb') as chunk:
            final_file.write(chunk.read())

   return conf, raw_path, json_path

