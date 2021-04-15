# -*- coding: utf-8 -*-
# @Time : 2021/4/15 11:37
# @Author : zj
# @File : wechat_publish.py
# @Project : spider_publish
import random
import time

import markdown
import requests
import arrow

from lxml import etree
from requests_toolbelt import MultipartEncoder
from app_doc.spider.utils.tools import headers_to_dict


# 微信公众号文章分发
class WeChatPublish:
    def __init__(self, cookie):
        """
        @param cookie:
        """
        self.sess = requests.session()
        base_header = f"""
           
        """
        self.sess.headers = headers_to_dict(base_header)
