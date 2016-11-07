from __future__ import absolute_import, division, print_function

from urllib2 import urlopen, Request, HTTPError

import base64
import logging
import json
import os
import hashlib


class B2CredentialsNotSpecified(ValueError):
  pass


class B2(object):
  AUTHORIZE_ACCOUNT_URL = "https://api.backblaze.com/b2api/v1/b2_authorize_account"

  DEFAULT_B2_ACCOUNT_ID = os.environ.get("B2_ACCOUNT_ID")
  DEFAULT_B2_APPLICATION_KEY = os.environ.get("B2_APPLICATION_KEY")
  DEFAULT_B2_BUCKET_ID = os.environ.get("B2_BUCKET_ID")

  def __init__(self, account_id=None, application_key=None, bucket_id=None):
    self.account_id = account_id or self.DEFAULT_B2_ACCOUNT_ID
    self.application_key = application_key or self.DEFAULT_B2_APPLICATION_KEY
    self.bucket_id = bucket_id or self.DEFAULT_B2_BUCKET_ID

    if not self.account_id:
      raise B2CredentialsNotSpecified("B2_ACCOUNT_ID is not specified")

    if not self.application_key:
      raise B2CredentialsNotSpecified("B2_APPLICATION_KEY is not specified")

    if not self.bucket_id:
      raise B2CredentialsNotSpecified("B2_BUCKET_ID is not specified")

    self.logger = logging.getLogger("minb2")
    self.auth_account()

  def auth_account(self):
    encoded_auth = "{0}:{1}".format(self.account_id, self.application_key)
    encoded_auth = base64.b64encode(encoded_auth.encode("utf-8"))
    headers = {
      "Authorization": "Basic {0}".format(encoded_auth.decode("utf-8")),
    }

    request = Request(
      self.AUTHORIZE_ACCOUNT_URL,
      headers=headers,
    )

    response = urlopen(request)
    response_data = json.loads(response.read().decode("utf-8"))
    response.close()

    self.auth_token = response_data["authorizationToken"]
    self.api_url = response_data["apiUrl"]
    self.download_url = response_data["downloadUrl"]

  def make_generic_api_request(self, url, data, headers=None, retried=False):
    if headers is None:
      headers = {}

    headers["Authorization"] = self.auth_token

    request = Request(
      self.url(url),
      data,
      headers=headers
    )

    self.logger.debug("making request to {}: {}".format(url, data))
    try:
      response = urlopen(request)
    except HTTPError as e:
      # Reauthenticate if we get a 401 as token will expire.
      if not retried and e.code == 401:
        self.logger.warn("401 for {}, reauthenticating...".format(url))
        self.auth_account()
        return self.make_generic_api_request(url, data, headers, retried=True)
      else:
        raise e

    response_data = json.loads(response.read().decode("utf-8"))
    response.close()
    return response_data

  def get_file_info(self, file_id):
    return self.make_generic_api_request(
      "/b2api/v1/b2_get_file_info",
      json.dumps({"fileId": file_id}).encode("utf-8")
    )

  def list_file_names(self, start_file_name):
    original_start_file_name = start_file_name
    number_of_files = 1
    while start_file_name and number_of_files:
      data = {
        "bucketId": self.bucket_id,
        "startFileName": start_file_name,
      }

      response_data = self.make_generic_api_request(
        "/b2api/v1/b2_list_file_names",
        json.dumps(data).encode("utf-8")
      )

      number_of_files = len(response_data["files"])

      for fileinfo in response_data["files"]:
        if not fileinfo["fileName"].startswith(original_start_file_name):
          continue

        yield fileinfo

      start_file_name = response_data["nextFileName"]
      if start_file_name and not start_file_name.startswith(original_start_file_name):
        start_file_name = None

  def upload_request(self):
    response_data = self.make_generic_api_request(
      "/b2api/v1/b2_get_upload_url",
      json.dumps({"bucketId": self.bucket_id}).encode("utf-8")
    )
    return response_data["uploadUrl"], response_data["authorizationToken"]

  def upload_file(self, path, filename=None, content_type="b2/x-auto"):
    upload_url, upload_auth_token = self.upload_request()

    with open(path, "rb") as f:
      filedata = f.read()
      sha1data = hashlib.sha1(filedata).hexdigest()

    filesize = os.path.getsize(path)

    headers = {
      "Authorization": upload_auth_token,
      "X-Bz-File-Name": filename or os.path.basename(path),
      "Content-Type": content_type,
      "X-Bz-Content-Sha1": sha1data,
      "Content-Length": filesize
    }

    request = Request(upload_url, filedata, headers=headers)
    response = urlopen(request)
    response_data = json.loads(response.read().decode("utf-8"))
    response.close()

    return self.download_url + "/b2api/v1/b2_download_file_by_id?fileId=" + response_data["fileId"]

  def url(self, url_postfix):
    return "{0}{1}".format(self.api_url, url_postfix)
