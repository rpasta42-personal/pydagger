from downloader import download2
from downloader import misc

def json_from_url(url):
   return misc.json_from_url(url)

def download(url, download_dir, onProgress=None):
   if onProgress is None:
      onProgress = lambda curr, total: None
   conf, raw_path, json_path = download2.download(url, download_dir, onProgress)
   return conf, raw_path, json_path
