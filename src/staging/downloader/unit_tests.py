#!/usr/bin/env python
import unittest, xxhash
from downloader import download, download2
import pycloak.shellutils

#python -m unittest unit_tests.TestDownload.test_download_new

class TestDownload(unittest.TestCase):
   def setUp(self):
      #self.addCleanup(self.tearDown)
      pycloak.shellutils.mkdir('test')
      #self.update_url = 'http://updatertest/fake-update.update_info'
      self.update_url = 'https://icloak.org/kkave/50mb/test.update_info'
      print('Unit test setUp')

   def tearDown(self):
      pycloak.shellutils.rm('test')
      print('Unit test tearDown')

   def test_download_old(self):
      self.download_func = download.download
      self.run_test(False)
   def test_download_new(self):
      self.download_func = download2.download
      self.run_test(False)
   def test_download_old_threads(self):
      self.download_func = download.download
      self.run_test(True)
   def test_download_new_threads(self):
      self.download_func = download2.download
      self.run_test(True)

   def run_test(self, useThreads):
      def onProgress(curr, total):
         print('curr:%i; total:%i' % (curr, total))
      conf, raw_path, json_path = self.download_func(self.update_url, 'test', onProgress, useThreads)
      with open(raw_path, 'rb') as f:
         file_hash = xxhash.xxh64(f.read()).intdigest()
      self.assertEqual(conf['raw-hash'], file_hash)

