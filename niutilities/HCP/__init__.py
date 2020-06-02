import sys
import gi_HCP
import gs_HCP
import gp_HCP
import ge_HCP

__all__ = ["gi_HCP", "gs_HCP", "gp_HCP", "ge_HCP"]

class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
   def write(self, data):
       self.stream.write(data)
       self.stream.flush()
   def writelines(self, datas):
       self.stream.writelines(datas)
       self.stream.flush()
   def __getattr__(self, attr):
       return getattr(self.stream, attr)

sys.stdout = Unbuffered(sys.stdout)
