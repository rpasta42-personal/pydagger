

def dict_get_recursive(d, key, default):
   if key in d:
      return d[key]
   else:
      for k in d.keys():
         if key in k:
            return d[k]
   return default
