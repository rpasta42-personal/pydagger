class Result(object):

   def __init__(self, success=False, msg="", code=1, code_labelis={'0':'SUCCESS', '1': 'FAIL'}, **kwargs):
      self.success = success
      self.msg = msg
      self.code = code
      self.code_label = code_label
      self.args = kwargs

   def __str__(self):
      return "[{}] [{}] {}".format(
            "SUCCESS" if self.success else "FAIL",
            self.code_labels.get(self.code, 'UNKNOWN'),
            self.msg if msg is not None else '')

