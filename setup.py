#!/usr/bin/env python

from setuptools import setup, find_packages


setup(
  name="seafile-backup",
  version="0.1",
  description="seafile backup",
  author="Shuhao Wu",
  packages=list(find_packages()),
  entry_points={
    "console_scripts": [
      "seafile-backup-check-sha1 = seafile_backup.cmds:cmd_check_sha1_sum"
    ]
  }
)
