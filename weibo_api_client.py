#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from multiprocessing import Process
from threading import Thread
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

from unittest import TestCase

#from sqlalchemy import Column
#from sqlalchemy import Integer, String
#from sqlalchemy import create_engine
#from sqlalchemy.orm import sessionmaker
#from sqlalchemy.ext.declarative import declarative_base


#import mechanize

import weibo
from weibo import APIClient as WeiboAPIClient


__version__ = '1.0.0'
__author__ = 'Kevin Zhang (kevin.misc.10@gmail.com)'


LOGFMT = '%(asctime)-15s %(message)s'
DATEFMT = '%y/%m/%d %H:%M:%S.%f'
logging.basicConfig(format=LOGFMT, datefmt=DATEFMT, level=logging.DEBUG)


#db = "sqlite:///:memory:"
#engine = create_engine(db, echo=False)
#session = sessionmaker(bind=engine)
#
#user = WeiboUser()
#session.add(user)
##session.query(WeiboUser).filter_by(code="600333").first()
##session.commit()
#


weibo_token = {
    "key" : "3356415000",
    "secret" : "70eea2f2cd0e37184f0a37d155034c12",
    "code" : None,
    "access_token" : None,
    "expires_in" : 0
}

AUTH_URL = '''https://api.weibo.com/oauth2/authorize?redirect_uri=https%3A//api.weibo.com/oauth2/default.html&response_type=code&client_id=3356415000'''

WEIBO_IDS = (
    {
        'id' : 1897208167,         # mine
        'screen_name': 'haiyuzhang',
        'name': 'haiyuzhang',
    }, {
        'id' : 1962065563,         # tian
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


class APIThrottler(threading.Thread):
    def __init__(self):
        super(APIThrottler, self).__init__()

        self.max_api_calls_per_hour = 150
        #self.api_rate = float(self.max_api_calls_per_hour) / ONE_HOUR
        self.api_rate = ONE_HOUR / float(self.max_api_calls_per_hour)

        self.api_token_queue = Queue(maxsize=self.max_api_calls_per_hour)
        self.api_token_index = 0

        self.token_water_level = self.max_api_calls_per_hour 

        self.__run = True
        self.daemon = True

        return

    def run_v0(self):
        while self.__run:
            now = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
            print(now)
            self.api_token_queue.put('API Token: %d Timestamp %s' % (
                                     self.api_token_index, now))
            self.api_token_index += 1
            time.sleep(self.api_rate)

        return

    def run(self):
        while self.__run:
            now = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
            print(now)

            while self.token_water_level > 0:
                self.api_token_queue.put('API Token: %d Timestamp %s' % (
                                         self.api_token_index, now))
                self.token_water_level -= 1
                self.api_token_index += 1

            time.sleep(ONE_HOUR)
            self.token_water_level = self.max_api_calls_per_hour 

        return

    def request_token(self):
        access_token = self.api_token_queue.get()
        return access_token

    def stop(self):
        self.__run = False
        if self.is_alive():
            self.join()
        return


class APIThrottlerTest(TestCase):
    def setUp(self):
        global api_throttler

        if not hasattr(self, 'api_throttler'):
            self.api_throttler = APIThrottler()

        api_throttler = self.api_throttler

        return

    def test_run(self):
        self.api_throttler.start()

        time.sleep(2)

        ac = APIConsumer()

        begin = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
        print('Start requesting @ %s' % (begin))
        for i in range(2):
            self.assertTrue(ac.request_api())
        end = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
        print('Stop requesting @ %s' % (end))

        return

    def runTest(self):
        self.test_run()
        return

    def tearDown(self):
        self.api_throttler.stop()
        del self.api_throttler
        return


class APIConsumer(object):
    def __init__(self):
        global api_token_bucket
        global api_throttler
        self.logger = logging.getLogger('%s.%s' % (self.__module__,
                                        self.__class__.__name__))
        self.logger.setLevel(logging.NOTSET)

        super(APIConsumer, self).__init__()

        self.api_token_bucket = api_throttler
        return

    def request_api(self):
        self.logger.debug('\nRequesting an API')
        try:
            api_token = self.api_token_bucket.request_token()
            if 'API Token' in api_token:
                self.logger.debug('\nGranted: ' % api_token)
                return True
        except Exception as e:
            return False

        return False




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
        print headers
        return result

    def http_error_302(cls, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(cls, req, fp, code, msg, headers)
        result.status = code
        print headers
        return result

def get_cookie():
    cookies = cookielib.CookieJar()
    return urllib2.HTTPCookieProcessor(cookies)

def get_opener(proxy=False):
    rv=urllib2.build_opener(get_cookie(), SmartRedirectHandler())
    rv.addheaders = [('User-agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)')]
    return rv

APP_KEY = '3356415000'
APP_SECRET = "70eea2f2cd0e37184f0a37d155034c12"
CALLBACK_URL = 'https://api.weibo.com/oauth2/default.html'
USERID = 'kevin.misc.10@gmail.com'
USERPASSWD = '951753'


# token file path
save_access_token_file  = 'access_token.txt'
file_path = os.path.dirname(__file__) + os.path.sep
#access_token_file_path = file_path + save_access_token_file
access_token_file_path = "./" + save_access_token_file

client = WeiboAPIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)


def make_access_token():
    '''请求access token'''
    params = urllib.urlencode({'action':'submit','withOfficalFlag':'0','ticket':'','isLoginSina':'', \
        'response_type':'code', \
        'regCallback':'', \
        'redirect_uri':CALLBACK_URL, \
        'client_id':APP_KEY, \
        'state':'', \
        'from':'', \
        'userId':USERID, \
        'passwd':USERPASSWD, \
        })

    login_url = 'https://api.weibo.com/oauth2/authorize'

    url = client.get_authorize_url()
    content = urllib2.urlopen(url)
    if content:
        headers = { 'Referer' : url }
        request = urllib2.Request(login_url, params, headers)
        opener = get_opener(False)
        urllib2.install_opener(opener)
        try:
            f = opener.open(request)
            print f.headers.headers
            return_callback_url = f.geturl()
            print f.read()
        except urllib2.HTTPError, e:
            return_callback_url = e.geturl()
        code = return_callback_url.split('=')[1]
    token = client.request_access_token(code)
    save_access_token(token)

def save_access_token(token):
    '''将access token保存到本地'''
    f = open(access_token_file_path, 'w')
    f.write(token['access_token']+' ' + str(token['expires_in']))
    f.close()

@retry(3)
def apply_access_token():
    '''从本地读取及设置access token'''
    try:
        token = open(access_token_file_path, 'r').read().split()
        if len(token) != 2:
            make_access_token()
            return False
        # 过期验证
        access_token, expires_in = token
        try:
            client.set_access_token(access_token, expires_in)
        except StandardError, e:
            if hasattr(e, 'error'): 
                if e.error == 'expired_token':
                    # token过期重新生成
                    make_access_token()
            else:
                pass
    except:
        make_access_token()
    
    return False

if __name__ == "__main__":
    apply_access_token()

    # 以下为访问微博api的应用逻辑
    # 以接口访问状态为例
    status = client.get.account__rate_limit_status()
    print json.dumps(status)

class WeiboMiner(APIConsumer):
    def __init__(self):
        super(WeiboMiner, self).__init__()

        self.logger = logging.getLogger('%s.%s' % (self.__module__,
                                        self.__class__.__name__))
        self.logger.setLevel(logging.NOTSET)

        self.key = ''
        self.secret = ''
        self.code = ''
        self.access_token = ''
        self.expires_in = 0

        self.load_access_token()

        #self.update_token()

        #return

        if not self.authorize():
            if not self.request_access_token():
                self.logger.error('0x{_id:X}: Failed to get authorization'.format(
                                  _id=id(self), data=data))
                return

    def update_token(self):
        return

    def request_access_token(self):
        '''Request access token from Weibo API interface
        '''
        auth_url = self.api_client.get_authorize_url()

        resp = urllib2.urlopen(auth_url)
        print(resp.__class__.__name__)
        print(dir(resp))
        print(resp.url)
        print(resp.msg)
        print(resp.headers)
        print(resp.info)
        if isinstance(resp, urllib2.Request):
            print(resp)
            pass
        else:
            pass

        '''
        https://api.weibo.com/oauth2/authorize?redirect_uri=https%3A//api.weibo.com/oauth2/default.html&response_type=code&client_id=3356415000
        '''
        print('Open this URL in web browser:\n%s' % auth_url)

        self.code = raw_input('Paste access_token here:>')

        r = self.api_client.request_access_token(self.code)
        self.logger.debug(r)
        access_token, expire_in = r.access_token, r.expires_in
        self.api_client.set_access_token(access_token, expire_in)

        self.update_access_token(self.access_token)

        return True

    def update_access_token(self, access_token, expires_in=None):
        '''Update access token and save it into access_token file
        '''
        self.access_token = access_token
        self.expires_in = expires_in

        if not access_token:
            self.logger.error('0x{_id:X}: No access token was granted'.format(
                              _id=id(self)))
            return False

        with open('access_token.json', 'rw+') as token_file:
            data = json.load(token_file)
            data['access_token'] = access_token
            token_file.seek(0)
            token_file.truncate()
            json.dump(data, token_file, indent=4)

        return

    def load_access_token(self):
        with open('access_token.json', 'r') as token_file:
            data = json.load(token_file)
            self.logger.debug('0x{_id:X}: {data}'.format(_id=id(self),
                              data=data))

            try:
                self.key = data['key']
                self.secret = data['secret']
                self.code = data['code']
                self.access_token = data['access_token']
                self.expire_in = data['expire_in']
            except KeyError as e:
                self.logger.error('0x{_id:X}: {e}'.format(_id=id(self), e=e))
                return

        return self.access_token

    def authorize(self):
        '''Get authorization from Weibo using OAuth2
        '''

        self.api_client = WeiboAPIClient(app_key=self.key,
                app_secret=self.secret,
                redirect_uri=CALLBACK_URL)
        print(self.access_token, self.expires_in)
        self.api_client.set_access_token(self.access_token,
                                              self.expires_in)

        return True
        #return False

    def dig(self):
        params = {'uid' : 1073610035, 'count' : 1000}

        try:
            friend_ids = self.api_client.friendships.friends.ids.get(**params)
        except weibo.APIError as e:
            self.logger.error(e)
            return

        for _id in friend_ids['ids']:
            params = {'uid' : _id}
            try:
                if not self.request_api():
                    self.logger.error('Failed to get api token')
                    break
                user_info = self.api_client.users.show.get(**params)
                self.logger.debug('0x{0:X} {1} {2}'.format(id(self),
                                  user_info['id'], user_info['screen_name']))
            except UnicodeError as e:
                print(user_info)
                pass
            except weibo.APIError as e:
                self.logger.error(e)
                pass

        return

    def login(self):
        return;

        self.br = mechanize.Browser()
        self.br.set_handle_robots(False)
        #self.br.set_handle_refresh(False)
        self.br.addheaders = [('User-Agent', 'Mozilla/5.0 Chrome/26.0.1410.64 Safari/537.31')]
        url_login = 'http://login.sina.com.cn'

        resp = self.br.open(url_login)
        print(resp.read())

        for form in self.br.forms():
            print('Form name: %s' % form.name)
            print(form)

        self.br.form = list(self.br.forms())[0]

        for control in self.br.form.controls:
            print(control)
            try:
                value = self.br[control.name]
                print('type:%s, name:%s, value:%s' % (control.type,
                      control.name, value))
            except ValueError as e:
                pass

        control_username = self.br.form.find_control('username')
        control_username.value = 'kevin.misc.10@gmail.com'
        control_password = self.br.form.find_control('password')
        control_password.value = '951753'

        resp = self.br.submit()
        html = resp.read()
        print(html)

        return


class WeiboMinerTest(TestCase):
    def setUp(self):
        self.miner = WeiboMiner()

        return

    def test_update_access_token(self):
        access_token = '1234567890'
        self.miner.update_access_token(access_token)

        self.assertEqual(access_token, self.miner.load_access_token())

        return

    def test_load_access_token(self):
        access_token = self.miner.load_access_token()
        print(access_token)
        #self.assertIsNone(self.miner.load_access_token())
        return

    def test_login(self):
        self.miner.login()
        return

    def runTest(self, output=None):
        #self.test_load_access_token()
        #self.test_update_access_token()
        self.test_login()
        return

    def tearDown(self):
        del self.miner
        return


api_throttler = APIThrottler()


def main():
    global api_throttler

    api_throttler.start()

    weibo_miner = WeiboMiner()
    weibo_miner.dig()
    api_throttler.stop()

    return

def test():
    user_info = {'bi_followers_count': 476,
                 'domain': u'yimaobuba',
                 'avatar_large': u'http://tp2.sinaimg.cn/1648237865/180/5637076046/1',
                 'block_word': 1,
                 'statuses_count': 9323,
                 'allow_all_comment': True,
                 'id': 1648237865,
                 'city': u'45',
                 'province': u'400',
                 'follow_me': False,
                 'verified_reason': u'',
                 'followers_count': 1194499,
                 'location': u'\u6d77\u5916 \u6c99\u7279\u963f\u62c9\u4f2f',
                 'mbtype': 12,
                 'profile_url': u'yimaobuba',
                 'status': {
                     'reposts_count': 0,
                     'favorited': False,
                     'truncated': False,
                     'text': u'\u6709\u5f88\u591a\u670b\u53cb\u90fd\u62c5\u5fc3\u5b69\u5b50\u8d70\u5931\u6216\u8005\u88ab\u62d0\u5356\uff0c\u8fd8\u6709\u5bb6\u91cc\u6709\u8001\u4eba\u6709\u8001\u5e74\u75f4\u5446\u75c7\u7684\u5bb6\u5ead\u3002\u6211\u770b\u5230\u6dd8\u5b9d\u4e0a\u6709\u5356GPS\u5b9a\u4f4d\u8ffd\u8e2a\u624b\u8868\uff0c\u53ef\u4ee5\u901a\u8fc7\u7535\u8111\u67e5\u8be2\u6234\u8868\u8005\u7684\u4f4d\u7f6e\uff0c\u751a\u81f3\u8fd8\u53ef\u4ee5\u5728\u5730\u56fe\u4e0a\u753b\u51fa\u4e00\u4e2a\u8303\u56f4\uff08\u5982\u81ea\u5df1\u7684\u5c0f\u533a\uff09\uff0c\u6234\u8868\u8005\u51fa\u4e86\u5c31\u81ea\u52a8\u53d1\u77ed\u4fe1\u5230\u5176\u4ed6\u624b\u673a\u62a5\u8b66\uff0c\u542c\u7740\u529f\u80fd\u633a\u5168\u53ea\u8981\u516d\u767e\u5757\u3002\u6709\u4eba\u4f7f\u7528\u6216\u8005\u5c1d\u8bd5\u8fc7\uff0c\u89c9\u5f97\u597d\u7528\u9760\u8c31\u5417\uff1f',
                     'created_at': u'Sun May 05 09:17:05 +0800 2013',
                     'mlevel': 0,
                     'idstr': u'3574524966139079',
                     'mid': u'3574524966139079',
                     'visible': {'type': 0, 'list_id': 0},
                     'attitudes_count': 0,
                     'pic_urls': [],
                     'in_reply_to_screen_name': u'',
                     'source': u'<a href="http://weibo.com/" rel="nofollow">\u65b0\u6d6a\u5fae\u535a</a>',
                     'in_reply_to_status_id': u'',
                     'comments_count': 0,
                     'geo': None,
                     'id': 3574524966139079L,
                     'in_reply_to_user_id': u''
                 },
                 'star': 0,
                 'description': u'\u4ee5\u7f3a\u5fb7\u670d\u4eba',
                 'friends_count': 527,
                 'online_status': 1,
                 'mbrank': 4,
                 'idstr': u'1648237865',
                 'profile_image_url': u'http://tp2.sinaimg.cn/1648237865/50/5637076046/1',
                 'allow_all_act_msg': False,
                 'verified': False,
                 'geo_enabled': False,
                 'screen_name': u'\u4e00\u6bdb\u4e0d\u62d4\u5927\u5e08',
                 'lang': u'zh-cn',
                 'weihao': u'',
                 'remark': u'',
                 'favourites_count': 13,
                 'name': u'\u4e00\u6bdb\u4e0d\u62d4\u5927\u5e08',
                 'url': u'http://beizhicheng.blog.caixin.cn/',
                 'gender': u'm',
                 'created_at': u'Wed Dec 23 22:01:12 +0800 2009',
                 'verified_type': -1,
                 'following': False
            }

    for k, v in user_info.items():
        if isinstance(v, dict):
            for k, v in user_info.items():
                print('%s - %s' % (k, v))
        else:
            print(k, v)
    return


if __name__ == '__main__':
    main()
    #test()

