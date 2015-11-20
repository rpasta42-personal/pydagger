#!/usr/bin/python3
#import brotli
import argparse, xxhash, json, os
from pycloak import misc

def parse_args():
   parser = argparse.ArgumentParser()
   parser.add_argument('-s', '--chunk-size', dest='size', help='Specify chunk size in kilobytes (default 1024 or 1 MB)')
   parser.add_argument('-o', '--out-json', dest='output', help='where to store update info (default is "<FILE>.update_info")')
   parser.add_argument('-c', '--compress-type', dest='compress', help='compress=0 (none), compress=1 (whole image) and compress=2 (chunk)')
   parser.add_argument('-e', '--extra-json', dest='extras_path', help='Add extra json read from extra json file')
   #parser.add_argument('-d', '--data-dir', dest='data_dir', help='which directory to store update data and hashes in')
   parser.add_argument('update_file', metavar='raw-update', help='Raw update file from which we generate update')
   parser.add_argument('version', metavar='version', help='icloak version')
   args = parser.parse_args()
   return args

args = parse_args()

block_size = args.size
version = args.version #timestamps instead?. -1 means always update
info_path = args.output
raw_path = args.update_file
compress = args.compress
extra_json_path = args.extras_path

if block_size is None:
   block_size = 1024
else:
   block_size = int(block_size)
block_size = block_size * 1024

if info_path is None:
   info_path = '%s.update_info' % raw_path

if compress is not None:
   compress = int(compress, 10)
if compress is None or compress < 0 or compress > 2:
   compress = 0

if extra_json_path == None:
   extra_json = None
else:
   extra_json = misc.read_conf(extra_json_path)
   print('Got extra json')

print('Compression option = %r' % compress)
print('Chunk size = %r' % block_size)
print('Output json = %s' % info_path)
print('Raw file = %s' % raw_path)
print('Version = %s' % version)

def get_whole_file_hash(file_name):
   with open(file_name, 'rb') as f:
      return xxhash.xxh64(f.read()).digest()

def get_hashes(file_name, block_size):
   hashes = []
   i = 0

   with open(file_name, 'rb') as f:
      while True:
         chunk = f.read(block_size)
         if not chunk:
            break
         chunk_hash = xxhash.xxh64(chunk).intdigest()
         hashes.append(chunk_hash)
         i = i+1
   #hashes_str = ''
   #for item in hashes:
   #   hashes_str += str(item) + '\n'
   return json.dumps(hashes), i

def compress_by_chunk(filename_in, filename_out, block_size):
   with open(filename_in, 'rb') as f_in, open(filename_out, 'wb') as f_out:
      while True:
         chunk = f_in.read(block_size)
         if not chunk:
            break
         compressed = brotli.compress(chunk)
         f_out.write(compressed)

def compress_whole(filename_in, filename_out):
   with open(filename_in, 'rb') as f_in, open(filename_out, 'wb') as f_out:
      f_out.write(brotli.compress(f_in.read()))

if compress == 0:
   #TODO: big_hash = get_whole_file_hash(raw_path)
   hashes, num_hashes = get_hashes(raw_path, block_size)
   hash_path = info_path + '.hashes'
   misc.write_file(hash_path, hashes)
elif compress == 1 or compress == 2:
   print('compression not supported yet')
   sys.exit(1)
   bro_path = raw_path + '.brotli'
   hash_path = bro_path + '.hashes'
   if compress == 1:
      compress_by_chunk(raw_path, bro_path, block_size)
   elif compress == 2:
      compress_whole(raw_path, bro_path)
   hashes, num_hashes = get_hashes(bro_path, block_size)
   misc.write_file(hash_path, hashes)
else:
   print('bad compression option %s' % str(compress))

json_conf = {
   'block-size'   : block_size,
   'raw-file'     : raw_path,
   'raw-size'     : os.path.getsize(raw_path), #os.stat(raw_path).st_size
   'compression'  : compress,
   'version'      : version,
   'progress'     : 0,
   'num-hashes'   : num_hashes,
   #'raw-hash'     : big_hash, #TODO: need this for unit tests but actual image is too big to digest
   'extra-json'   : extra_json
}

misc.write_conf(info_path, json_conf)


