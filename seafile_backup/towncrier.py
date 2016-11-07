from __future__ import print_function

from urllib2 import urlopen, Request

import os
import traceback

# Implementation of API to Towncrier
# https://gitlab.com/shuhao/towncrier
#
# This is used to send email reports all day.
# This is used because I use it to aggregate all of my notifications from
# my other servers and such. Sending via raw SMTP is also acceptable but
# that needs additional code and configuration.
#
# TODO: refactor this so we can have multiple notification backend, which
# allow people to use SMTP from Gmail or something like that.
#
# Specifically: use a class rather than a module

TOWNCRIER_BASE_URL = os.environ.get("TOWNCRIER_BASE_URL", "").strip()
AUTH_TOKEN = os.environ.get("TOWNCRIER_AUTH_TOKEN", "").strip()


def name():
  return "Towncrier"


def available():
  return TOWNCRIER_BASE_URL and AUTH_TOKEN


def notify_exception(title, e, logs=""):
  body = """
Crashed with exception {0}:

{1}

{2}
  """.strip().format(e, traceback.format_exc(), logs)

  notify("[{0}] {1}".format(e.__class__.__name__, title), body, tags=["exception"], channel="immediate")


def notify(subject, body, tags=[], priority="normal", channel="immediate"):
  url = TOWNCRIER_BASE_URL + "/notifications/" + channel
  headers = {
    "Authorization": "Token token=%s" % AUTH_TOKEN,
    "X-Towncrier-Subject": subject,
    "X-Towncrier-Tags": ",".join(tags),
    "X-Towncrier-Priority": priority,
    "Content-Type": "text/plain",
  }

  print()
  print("Towncrier notification triggered")
  print("Sending the following email...")
  print()
  for k, v in headers.items():
    print("{0}: {1}".format(k, v))
  print()
  print(body)

  if not available() or os.environ.get("NOTIFIERS_DISABLED"):
    print()
    print("WARN: Towncrier (notification) not available.")
    print("WARN: NO EMAIL WAS SENT!")
    print()
    return

  req = Request(url, body.encode("utf-8"), headers)
  resp = urlopen(req)
  print("Posted to towncrier: {0}".format(resp.code))
