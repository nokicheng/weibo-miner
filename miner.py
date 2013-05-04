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

#from sqlalchemy import Column
#from sqlalchemy import Integer, String
#from sqlalchemy import create_engine
#from sqlalchemy.orm import sessionmaker
#from sqlalchemy.ext.declarative import declarative_base


from weibo import APIClient as WeiboAPIClient

#from rauth.service import OAuth2Service

#Base = declarative_base()


#
from weibo import APIClient as WeiboAPIClient
#
from rauth.service import OAuth2Service
#
#Base = declarative_base()
#
#
#class WeiboUser(Base):
#    __tablename__ = "stock"
#
#    code = Column(String, primary_key=True)
#    name = Column(String, unique=True)
#    quantity = Column(Integer)
#    price = Column(Integer)
#    
#    TRADE_STATE_A = 'TRADE_ACCEPTED'
#    TRADE_STATE_S = 'TRADE_SUCCESSED'
#    TRADE_STATE_W = 'TRADE_WAITING'
#    TRADE_STATE_F = 'TRADE_FAILED'
#
#    def __init__(self, code, name, price=0, quantity=0):
#        self.code = code
#        self.name = name
#        self.price = price
#        self.quantity = quantity
#
#        self.buy_queue = []
#        self.sell_queue = []
#
#        self.request_matcher = RequestMatcher(self)
#        self.request_matcher.run()
#
#        return
#
#    def __str__(self):
#        return '%s-%d-%d' % (self.name, self.price, self.quantity)
#
#    def __repr__(self):
#        return "%s<%s-%d-%d>" % (self.__class__.__name__, self.name, self.price,
#               self.quantity)
#
#    def trade(self, request=TradeRequest()):
#        """Try trading, return trading result.
#        """
#        state = TRADE_STATE_W
#        try:
#            stock = self.stock_pool[request.name]
#        except KeyError, e:
#            state = TRADE_STATE_F
#            return state
#
#        stock.request_enqueu(request)
#        if not stock.match():       # If a successful match doesn't occur,
#            state = TRADE_STATE_W   # waiting
#        else:
#            state = TRADE_STATE_S
#
#        return state
#
#def set_db(db_new):
#    global db
#
#    db = db_new
#
#    return True
#
#
#
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

code = None
code = '4f66d6fea424771dd617dbf4adc3cd61'
access_token = None
access_token = '2.00jVU5ECorKJfDdd088997374LTVzD'

expires_in = 1525003488

def auth_v0():
    weibo = OAuth2Service(name='weibo',
                          client_id=client_key,
                          client_secret=client_secret,
                          access_token_url='https://api.weibo.com/oauth2/access_token',
                          authorize_url='https://api.weibo.com/oauth2/authorize',
                          base_url='https://api.weibo.com')

    if not access_token:
        redirect_uri = 'https://api.weibo.com/oauth2/default.html'
        params = {'response_type' : 'token', 'scope' : 'email', 'redirect_uri' : redirect_uri}
        authorize_url = weibo.get_authorize_url(**params)
        print(authorize_url)
        # token is correct though
    else:
        session = weibo.get_session(access_token)
        email = session.get('https://api.weibo.com/2/account/profile/email.json',
        params={'access_token' : access_token})
        print(email)
        pass

    return

def weibo_auth():
    global code, access_token, expires_in

    print(1212121212)

def auth_v1():
    global code, access_token, expires_in

    redirect_uri = 'https://api.weibo.com/oauth2/default.html'
    client = WeiboAPIClient(app_key=client_key, app_secret=client_secret,
                       redirect_uri=redirect_uri)
    if (not code) and (not access_token):
        print('Open this URL in web browser:\n%s' % client.get_authorize_url())
        return
        print(client.get_authorize_url())
    elif not access_token:
        r = client.request_access_token(code)
        access_token = r.access_token
        expires_in = r.expires_in
        logging.debug(access_token)
        logging.debug(expires_in)
        return
    else:
        client.set_access_token(access_token, expires_in)
        ##print(client.statuses.user_timeline.get())
        ##print(client.account.profile.email.get())
        #params = {'screen_name':'haiyuzhang'}
        pass

    return client


WEIBO_IDS = {
    1897208167,         # mine
    1962065563,         # tian
}

def api_throttlign():
    return

def dig():
    global weibo_api_client

    params = {'uid' : 1962065563, 'count' : 1000}
    friend_ids = weibo_api_client.friendships.friends.ids.get(**params)

    for _id in friend_ids['ids']:
        params = {'uid' : _id}
        print(_id)
        try:
            user_info = weibo_api_client.users.show.get(**params)
            print(user_info['screen_name'])
        except Exception as e:
            print(e)
        pass

    return

def main():
    global weibo_api_client

    #auth_v0()
    weibo_api_client = weibo_auth()
    dig()

    return
        print(access_token)
        print(expires_in)
    else:
        client.set_access_token(access_token, expires_in)
        #print(client.statuses.user_timeline.get())
        #print(client.account.profile.email.get())
        params = {'screen_name':'haiyuzhang'}
        #params = {'uid' : 1897208167}
        params = {'uid' : 1962065563}
        print(client.friendships.friends.get(**params))
        print(client.users.show.get(**params))
        pass
    return

def main():
    #auth_v0()
    auth_v1()

if __name__ == "__main__":
    #unittest.main()
    main()

