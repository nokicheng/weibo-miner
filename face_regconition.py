#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''Search all image for faces
'''

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

from sqlalchemy import Column
from sqlalchemy import Integer, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from weibo import APIClient as WeiboAPIClient

Base = declarative_base()


class WeiboUser(Base):
    __tablename__ = "stock"

    code = Column(String, primary_key=True)
    name = Column(String, unique=True)
    quantity = Column(Integer)
    price = Column(Integer)
    
    TRADE_STATE_A = 'TRADE_ACCEPTED'
    TRADE_STATE_S = 'TRADE_SUCCESSED'
    TRADE_STATE_W = 'TRADE_WAITING'
    TRADE_STATE_F = 'TRADE_FAILED'

    def __init__(self, code, name, price=0, quantity=0):
        self.code = code
        self.name = name
        self.price = price
        self.quantity = quantity

        self.buy_queue = []
        self.sell_queue = []

        self.request_matcher = RequestMatcher(self)
        self.request_matcher.run()

        return

    def __str__(self):
        return '%s-%d-%d' % (self.name, self.price, self.quantity)

    def __repr__(self):
        return "%s<%s-%d-%d>" % (self.__class__.__name__, self.name, self.price,
               self.quantity)

    def trade(self, request=TradeRequest()):
        """Try trading, return trading result.
        """
        state = TRADE_STATE_W
        try:
            stock = self.stock_pool[request.name]
        except KeyError, e:
            state = TRADE_STATE_F
            return state

        stock.request_enqueu(request)
        if not stock.match():       # If a successful match doesn't occur,
            state = TRADE_STATE_W   # waiting
        else:
            state = TRADE_STATE_S

        return state

def set_db(db_new):
    global db

    db = db_new

    return True


if __name__ == "__main__":
    unittest.main()

