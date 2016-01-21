import requests

def check_connectivity(url = "http://icloak.me", expect_code = 200, proxy=None, verify=False):
   """Simple connectivity check. We request a remote server(defaults icloak.me) and return True on status 200(default)"""
   try:
      r = requests.get(url)
      if r.status_code == expect_code:
         return True
      return False
   except:
      return False

if __name__ == "__main__":
   if check_connectivity():
      print("Connected!")
   else:
      print("Not connected")
