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


#from sqlalchemy import Column
#from sqlalchemy import Integer, String
#from sqlalchemy import create_engine
#from sqlalchemy.orm import sessionmaker
#from sqlalchemy.ext.declarative import declarative_base

from weibo_api_client import weibo_api_client


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


class WeiboMiner(object):
    def __init__(self):
        #super(object, self).__init__()

        self.logger = logging.getLogger('%s.%s' % (self.__module__,
                                        self.__class__.__name__))
        self.logger.setLevel(logging.NOTSET)

        self.api_client = weibo_api_client
        return

    def fetch_followers(self):
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


    def find_closest_friends(self, uid=None):
        '''Find the closes friends of an user
        '''
        params = {'uid' : 1073610035, 'count' : 10}

        # 1. fetch 30 post
        statuses = self.api_client.get.statuses__bilateral_timeline(**params)
        for s in statuses['statuses']:
            print(s['id'])
            print(s['text'].encode('utf-8'))
            print(s['user']['id'])
            print(s['user']['screen_name'].encode('utf-8'))
            print('---------------------------')
            #json.dumps(s)
        # 2. fetch all comments of these post
        # 3. fetch user id of these comments

        return


class WeiboMinerTest(unittest.TestCase):
    def setUp(self):
        self.miner = WeiboMiner()

        return


def main():
    weibo_miner = WeiboMiner()
    weibo_miner.find_closest_friends()

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

