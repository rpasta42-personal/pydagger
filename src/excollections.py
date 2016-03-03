

def dict_get_recursive(d, key, default):
   if key in d:
      return d[key]
   else:
      for k in d.keys():
         if key in k:
            return d[k]
   return default

#subtract a list from a list
def sub_lst(lst, to_subtract):
    ret = []
    for item in lst:
        if not item in to_subtract:
            ret.append(item)
    return ret
