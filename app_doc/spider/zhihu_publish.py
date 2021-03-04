# -*- coding: utf-8 -*-
# @Time : 2021/3/3 10:07
# @Author : zj
# @File : zhihu_publish.py
# @Project : spider_publish
import json
import os
import time
import random

import requests
import hmac
import base64
import execjs
from hashlib import sha256
from app_doc.spider.utils.tools import headers_to_dict
from lxml import etree


class ZhiHuPublish:
    def __init__(self, cookie):
        self.sess = requests.session()
        self.cookie = cookie
        header = f"""
            accept: */*
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9
            content-type: application/json
            cookie: {cookie}
            origin: https://zhuanlan.zhihu.com
            referer: https://zhuanlan.zhihu.com/write
            user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36
        """
        self.sess.headers = headers_to_dict(header)

    # 获取文章 id 。知乎输入标题后会异步发送请求
    def get_article_id(self, title):
        url = 'https://zhuanlan.zhihu.com/api/articles/drafts'
        form_data = {
                     "title": title,
                     "delta_time": 0
                    }
        res = self.sess.post(url, json=form_data)
        # print('获取 art_id:', res.text)
        r_json = res.json()
        art_id = r_json.get('id')
        return art_id

    def get_article_tag(self, tags, art_id):
        tag_flag = True
        for i in tags.split(','):
            tag_url = f'https://zhuanlan.zhihu.com/api/autocomplete/topics?token={i}&max_matches=5&use_similar=0&topic_filter=1'
            res = self.sess.get(tag_url)
            # print('查询标签结果：', res.text)
            if res.status_code == 200:
                json_data = res.json()[0]
                post_tag_url = f'https://zhuanlan.zhihu.com/api/articles/{art_id}/topics'
                res_tag = self.sess.post(url=post_tag_url, json=json_data)
                # print('上传标签：', res_tag.text)
                if res_tag.status_code == 200:
                    tag_flag = True
                else:
                    tag_flag = False
            else:
                tag_flag = False
        return tag_flag

    def publish_content(self, tags, title, content):
        art_id = self.get_article_id(title)
        publish_url = f'https://zhuanlan.zhihu.com/api/articles/{art_id}/draft'
        referer = f'https://zhuanlan.zhihu.com/p/{art_id}/edit'
        content = self.img_upload(content, referer)
        form_data = {"content": content, "delta_time": 37}
        res = self.sess.patch(url=publish_url, json=form_data)
        # print('实时保存结果：', res.text)
        if res.status_code == 200:
            tag_result = self.get_article_tag(tags, art_id)
            if tag_result:
                real_publish_url = f'https://zhuanlan.zhihu.com/api/articles/{art_id}/publish'
                json_data = {
                             "column": None,
                             "commentPermission": "anyone",
                             "disclaimer_status": "close",
                             "disclaimer_type": "none"
                            }
                res_push = self.sess.put(real_publish_url, json=json_data)
                # print(res_push.text, '发布结果')
                if res_push.status_code == 200:
                    return res_push.text
        return False

    def img_upload(self, content, referer):
        img_header = f"""
            accept: */*
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9
            x-requested-with:fetch
            cookie: {self.cookie}
            origin: https://zhuanlan.zhihu.com
            referer: {referer}
            user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36
        """
        # 图片需要上传到 csdn，否则发布的文章没有图片
        upload_url = 'https://zhuanlan.zhihu.com/api/uploaded_images'
        self.sess.headers = headers_to_dict(img_header)
        content_html = etree.HTML(content)
        src_list = content_html.xpath('//img/@src')
        for src in src_list:
            while 1:
                files = {'url': (None, src), 'source': (None, 'article')}
                res = self.sess.post(url=upload_url, files=files)
                # print('上传图片结果：', res.text)
                if res.text:
                    r_json = res.json()
                    # 图片在文章中本来就不存在
                    if r_json.get('code') == 400:
                        return content
                    img_url = r_json.get('watermark_src')
                    content = content.replace(src, img_url)
                    time.sleep(random.random() * 0.1)
                    break
        return content

    def del_doc(self, art_url: str):
        art_id = art_url.rsplit('/', 1)[1]
        del_url = f'https://www.zhihu.com/api/v4/articles/{art_id}'
        res = self.sess.delete(del_url)
        if res.text:
            r_json = res.json()
            success = r_json.get('success')

            if success:
                return True
        return False