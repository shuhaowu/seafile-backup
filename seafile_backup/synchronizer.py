from __future__ import absolute_import, division, print_function

from .utils import Commands


class Synchronizer(Commands):
  @classmethod
  def synchronize(cls):
    parser, args = cls.parser_with_local_and_remote_path("synchronizes a directory with b2")
    cls.run_cmd("_synchronize", args)

  def _synchronize(self, args):
    pass
