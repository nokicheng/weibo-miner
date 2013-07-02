#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import socket
import time
import logging
import threading
import random
import unittest
import errno
from Queue import Queue
from datetime import datetime
import json

import cookielib
import urllib
import urllib2

import math
import time

from weibo_api import APIClient


__version__ = '1.0.0'
__author__ = 'Kevin Zhang (kevin.misc.10@gmail.com)'


LOGFMT = '%(asctime)-15s %(message)s'
DATEFMT = '%y/%m/%d %H:%M:%S.%f'
logging.basicConfig(format=LOGFMT, datefmt=DATEFMT, level=logging.DEBUG)


__all__ = ['weibo_api_client']


WEIBO_IDS = (
    {
        'id' : 1897208167,
        'screen_name': 'haiyuzhang',
        'name': 'haiyuzhang',
    }, {
        'id' : 1962065563,
        'screen_name': "米其林的肚肚皮",
        'name': "米其林的肚肚皮",
    }, {
        "id": 1073610035,
        "idstr": "1073610035",
        "screen_name": "范范要少吃饭饭",
        "name": "范范要少吃饭饭",
    }
)


ONE_SEC = 1
ONE_MINUTE = 60 * ONE_SEC
ONE_HOUR = 60 * ONE_MINUTE 


# Retry decorator with exponential backoff
def retry(tries, delay=1, backoff=2):
  """Retries a function or method until it returns True.
 
  delay sets the initial delay, and backoff sets how much the delay should
  lengthen after each failure. backoff must be greater than 1, or else it
  isn't really a backoff. tries must be at least 0, and delay greater than
  0."""

  if backoff <= 1:
    raise ValueError("backoff must be greater than 1")

  tries = math.floor(tries)
  if tries < 0:
    raise ValueError("tries must be 0 or greater")

  if delay <= 0:
    raise ValueError("delay must be greater than 0")

  def deco_retry(f):
    def f_retry(*args, **kwargs):
      mtries, mdelay = tries, delay # make mutable

      rv = f(*args, **kwargs) # first attempt
      while mtries > 0:
        if rv == True or type(rv) == str: # Done on success ..
          return rv

        mtries -= 1      # consume an attempt
        time.sleep(mdelay) # wait...
        mdelay *= backoff  # make future wait longer

        rv = f(*args, **kwargs) # Try again

      return False # Ran out of tries :-(

    return f_retry # true decorator -> decorated function
  return deco_retry  # @retry(arg[, ...]) -> true decorator


class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(cls, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_301(cls, req, fp, code, msg, headers)
        result.status = code
        #print headers
        return result

    def http_error_302(cls, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(cls, req, fp, code, msg, headers)
        result.status = code
        #print headers
        return result

def get_cookie():
    cookies = cookielib.CookieJar()
    return urllib2.HTTPCookieProcessor(cookies)

def get_opener(proxy=False):
    rv=urllib2.build_opener(get_cookie(), SmartRedirectHandler())
    rv.addheaders = [('User-agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)')]
    return rv


# token file path
access_token_file  = 'access_token.json'
file_path = os.path.dirname(__file__) + os.path.sep
#access_token_file_path = file_path + save_access_token_file
access_token_file_path = "./" + access_token_file


def save_access_token(token):
    with open(access_token_file_path, 'rw+') as token_file:
        data = json.load(token_file)
        data['access_token'] = token['access_token']
        data['expires_in'] = token['expires_in']
        token_file.seek(0)
        token_file.truncate()
        json.dump(data, token_file, indent=4)

    return

def fetch_access_token(client, userid, passwd, app_key, callback_url):
    params = urllib.urlencode({         \
        'action':'submit',              \
        'withOfficalFlag':'0',          \
        'ticket':'','isLoginSina':'',   \
        'response_type':'code',         \
        'regCallback':'',               \
        'redirect_uri':callback_url,    \
        'client_id':app_key,            \
        'state':'',                     \
        'from':'',                      \
        'userId':userid,                \
        'passwd':passwd,            \
        })

    login_url = 'https://api.weibo.com/oauth2/authorize'

    url = client.get_authorize_url()
    content = urllib2.urlopen(url)
    if not content:
        return

    headers = { 'Referer' : url }
    request = urllib2.Request(login_url, params, headers)
    opener = get_opener(False)
    urllib2.install_opener(opener)
    try:
        f = opener.open(request)
        #print f.headers.headers
        return_callback_url = f.geturl()
        #print f.read()
    except urllib2.HTTPError, e:
        return_callback_url = e.geturl()

    code = return_callback_url.split('=')[1]

    token = client.request_access_token(code)
    client.set_access_token(token['access_token'], token['expires_in'])

    save_access_token(token)

    return


def create_api_client(token_path):
    with open(token_path, 'r') as token_file:
        try:
            data = json.load(token_file)
            userid = data['userid']
            passwd = data['passwd']
            app_key = data['app_key']
            app_secret = data['app_secret']
            code = data['code']
            access_token = data['access_token']
            expires_in = data['expires_in']
            #reset_time = data['reset_time']
            # TODO: get callback_url from json file
            #callback_url = data['callback_url']
            callback_url = 'https://api.weibo.com/oauth2/default.html'
        except KeyError as e:
            #self.logger.error('0x{_id:X}: {e}'.format(_id=id(self), e=e))
            return

    client = APIClient(app_key=app_key, app_secret=app_secret,
                       redirect_uri=callback_url)

    fetch_access_token(client, userid, passwd, app_key, callback_url)

    return client


weibo_api_client = create_api_client(access_token_file_path)

def test():
    status = weibo_api_client.get.account__rate_limit_status()
    print json.dumps(status)


if __name__ == '__main__':
    #unittest.main()
    test()

