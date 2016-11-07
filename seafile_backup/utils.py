from __future__ import absolute_import, division, print_function

import argparse
import logging
import os.path
import sys

from .minb2 import B2, B2CredentialsNotSpecified
from . import towncrier


class Commands(object):
  @classmethod
  def parser_with_local_and_remote_path(cls, description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("local_path", help="the local directory to the files")
    parser.add_argument("remote_path", help="the remote directory to the files")
    args = parser.parse_args()

    if not args.local_path or not os.path.isdir(args.local_path):
      print("ERROR: {} is not a valid local path.".format(args.local_path), file=sys.stderr)
      sys.exit(1)

    if not args.remote_path.endswith("/"):
      args.remote_path += "/"

    return parser, args

  @classmethod
  def run_cmd(cls, cmd_name, args):
    c = cls()

    try:
      getattr(c, cmd_name)(args)
    except Exception as e:
      towncrier.notify_exception("Failed to execute {}.{}".format(cls.__name__, cmd_name), e)

  def __init__(self):
    try:
      self.b2 = B2()
    except B2CredentialsNotSpecified as e:
      print("ERROR: {}".format(e), file=sys.stderr)
      sys.exit(1)

    self.logger = logging.getLogger(self.__class__.__name__)
