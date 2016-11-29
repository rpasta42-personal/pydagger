class Result(object):

   def __init__(self, success=False, msg="", code=1, code_labels={'0':'SUCCESS', '1': 'FAIL'}, **kwargs):
      self.success = success
      self.msg = msg
      self.code = code
      self.code_labels = code_labels
      self.args = kwargs

   def __str__(self):
      return "[{}] [{}] {}".format(
            "SUCCESS" if self.success else "FAIL",
            self.code_labels.get(str(self.code), 'UNKNOWN'),
            self.msg if self.msg is not None else '')

   def as_dict(self):
      return {
            "success": self.success,
            "msg": self.msg,
            "code": self.code,
            "code_labels": self.code_labels,
            "args": self.args
      }
