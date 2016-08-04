#! python2
# -*- coding:utf-8 -*-
import threading
import requests
from pyquery import PyQuery as pq


class Worker(threading.Thread):
