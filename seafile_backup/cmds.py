from __future__ import absolute_import, print_function

import logging

from .verifier import Verifier

logging.basicConfig(format="[%(asctime)s][%(levelname).1s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG)

cmd_check_sha1_sum = Verifier.check_sha1_sum
