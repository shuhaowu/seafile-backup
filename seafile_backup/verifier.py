from __future__ import absolute_import, division, print_function

import hashlib
import os.path
import sys

from .utils import Commands
from . import towncrier


class Verifier(Commands):
  @classmethod
  def check_sha1_sum(cls):
    parser, args = cls.parser_with_local_and_remote_path("checking sha1sum against b2 remote")
    cls.run_cmd("_check_sha1_sum", args)

  def _check_sha1_sum(self, args):
    self.logger.info("checking {} on remote bucket {} under path {}".format(args.local_path, self.b2.bucket_id, args.remote_path))
    remote_files = {}

    for i, fileinfo in enumerate(self.b2.list_file_names(args.remote_path)):
      filename = fileinfo["fileName"][len(args.remote_path):]
      remote_files[filename] = fileinfo

      errors = []

    for fn in os.listdir(args.local_path):
      if fn not in remote_files:
        errors.append("{}: not found".format(fn))
        self.logger.error(errors[-1])
        continue

      failed = False
      path = os.path.join(args.local_path, fn)
      size = os.path.getsize(path)
      if remote_files[fn]["contentLength"] != size:
        errors.append("{}: content length mismatched => {} (local) vs {} (remote)".format(fn, size, remote_files[fn]["contentLength"]))
        self.logger.error(errors[-1])
        failed = True

      sha1sum = self._sha1_file(path)
      remote_sha1 = remote_files[fn]["contentSha1"] or remote_files[fn]["fileInfo"]["large_file_sha1"]
      if remote_sha1 != sha1sum:
        errors.append("{}: sha1 mismatched => {} (local) vs {} (remote)".format(fn, sha1sum, remote_sha1))
        self.logger.error(errors[-1])
        failed = True

      if not failed:
        self.logger.info("{}: passed".format(fn))

    if len(errors) > 0:
      self.logger.error("errors occured during verification:")
      for error in errors:
        self.logger.error(" - {}".format(error))

      towncrier.notify("Failed to verify sha1sum against {}".format(args.remote_path), "\n".join(errors), tags=["exception"], channel="immediate")

      sys.exit(1)
    else:
      self.logger.info("VERIFICATION PASSED")

  def _sha1_file(self, path):
    sha = hashlib.sha1()

    with open(path, "rb") as f:
      while True:
        block = f.read(2**10)
        if not block:
          break
        sha.update(block)

    return sha.hexdigest()
