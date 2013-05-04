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

from unittest import TestCase

#from sqlalchemy import Column
#from sqlalchemy import Integer, String
#from sqlalchemy import create_engine
#from sqlalchemy.orm import sessionmaker
#from sqlalchemy.ext.declarative import declarative_base

import weibo
from weibo import APIClient as WeiboAPIClient

logging.basicConfig(level=logging.DEBUG)


#db = "sqlite:///:memory:"
#engine = create_engine(db, echo=False)
#session = sessionmaker(bind=engine)
#
#user = WeiboUser()
#session.add(user)
##session.query(WeiboUser).filter_by(code="600333").first()
##session.commit()
#

client_key = '3356415000'
client_secret = '70eea2f2cd0e37184f0a37d155034c12'


weibo_token = {
    "key" : "3356415000",
    "secret" : "70eea2f2cd0e37184f0a37d155034c12",
    "code" : None,
    "access_token" : None,
    "expires_in" : 0
}


WEIBO_IDS = {
    1897208167,         # mine
    1962065563,         # tian
}


one_sec = 1
one_hour = 60 * 60 * one_sec

class APIThrottler(threading.Thread):
    def __init__(self):
        super(APIThrottler, self).__init__()

        self.max_api_calls_per_hour = 150
        #self.api_rate = float(self.max_api_calls_per_hour) / one_hour
        self.api_rate = one_hour / float(self.max_api_calls_per_hour)

        self.api_token_queue = Queue(maxsize=self.max_api_calls_per_hour)
        self.api_token_index = 0

        self.token_water_level = self.max_api_calls_per_hour 

        self.__run = True

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

            time.sleep(one_hour)
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
        try:
            api_token = self.api_token_bucket.request_token()
            if 'API Token' in api_token:
                self.logger.debug(api_token)
                return True
        except Exception as e:
            return False

        return False

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

        if not self.authorize():
            if not self.request_access_token():
                self.logger.error('0x{_id:X}: Failed to get authorization'.format(
                                  _id=id(self), data=data))
                return

        return

    def request_access_token(self):
        '''Request access token from Weibo API interface
        '''
        print('Open this URL in web browser:\n%s' % \
              self.api_client.get_authorize_url())
        self.code = raw_input('Paste access_token here:>')

        r = self.api_client.request_access_token(self.code)
        self.logger.debug(r)
        access_token, expire_in = r.access_token, r.expires_in
        self.api_client.set_access_token(access_token, expire_in)

        self.update_access_token(self.access_token)

        return True

    def update_access_token(self, access_token, expire_in):
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

        redirect_uri = 'https://api.weibo.com/oauth2/default.html'
        self.api_client = WeiboAPIClient(app_key=self.key,
                                              app_secret=self.secret,
                                              redirect_uri=redirect_uri)
        print(self.access_token, self.expires_in)
        self.api_client.set_access_token(self.access_token,
                                              self.expires_in)

        return True
        #return False

    def dig(self):
        params = {'uid' : 1962065563, 'count' : 1000}
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
                print(_id)
                print(user_info['screen_name'])
            except weibo.APIError as e:
                self.logger.error(e)
                pass

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

    def runTest(self, output=None):
        self.test_load_access_token()
        self.test_update_access_token()
        return

    def tearDown(self):
        del self.miner
        return


def main():
    global api_throttler

    api_throttler = APIThrottler()
    api_throttler.start()

    weibo_miner = WeiboMiner()
    weibo_miner.dig()

    return

if __name__ == "__main__":
    main()

