# -*- coding: utf-8 -*-
# @Time : 2021/2/4 17:22
# @Author : zj
# @File : csdn_publish.py
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


class CSDNPublish:
    def __init__(self, cookie):
        self.sess = requests.session()
        self.cookie = cookie

    def gen_header(self, base_url):
        x_ca_nonce, signature = self._de_sign(base_url)
        header = f"""
                accept: */*
                accept-language: zh-CN,zh;q=0.9
                content-type: application/json
                cookie: {self.cookie}
                origin: https://editor.csdn.net
                referer: https://editor.csdn.net/
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36
                x-ca-key: 203803574
                x-ca-nonce: {x_ca_nonce}
                x-ca-signature: {signature}
                x-ca-signature-headers: x-ca-key,x-ca-nonce
            """
        return header

    def publish_content(self, tags, title, markdowncontent, content):
        self.markdowncontent, self.content = self.img_upload(markdowncontent=markdowncontent, content=content)
        base_url = "/blog-console-api/v3/mdeditor/saveArticle"
        self.sess.headers = headers_to_dict(self.gen_header(base_url))
        url = 'https://bizapi.csdn.net/blog-console-api/v3/mdeditor/saveArticle'
        form_data = {
            "title": title,
            "markdowncontent": self.markdowncontent,
            "content": self.content,
            "readType": "public",
            "tags": tags,
            "status": 0,
            "categories": "",
            "type": "original",
            "original_link": "",
            "authorized_status": False,
            "not_auto_saved": "1",
            "source": "pc_mdeditor"
        }
        res = self.sess.post(url=url, json=form_data)
        if res.text:
            return res.text
        return None

    def _de_sign(self, base_url):
        path = os.getcwd()
        path_js = path + '/app_doc/spider/web_js/csdn_x_ca.js'
        x_ca_nonce = execjs.compile(open(path_js, 'r', encoding='utf8').read()).call('f')
        appsecret = '9znpamsyl2c7cdrr9sas0le9vbc3r6ba'
        md5 = ''
        text_sign = ''
        text_sign += "POST" + '\n'
        text_sign += "*/*" + '\n'
        text_sign += md5 + '\n'
        text_sign += "application/json" + '\n'
        text_sign += "" + '\n'
        text_sign += "x-ca-key:203803574" + '\n'
        text_sign += f"x-ca-nonce:{x_ca_nonce}" + '\n'
        text_sign += base_url

        appsecret = appsecret.encode('utf-8')  # 秘钥
        data = text_sign.encode('utf-8')  # 加密数据
        signature = base64.b64encode(hmac.new(appsecret, data, digestmod=sha256).digest()).decode('utf8')
        return x_ca_nonce, signature

    def gen_random(self):

        seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        sa = []
        for i in range(8):
            sa.append(random.choice(seed))
        salt = ''.join(sa)
        return salt

    def img_upload(self, markdowncontent, content):
        # 图片需要上传到 csdn，否则发布的文章没有图片
        upload_url = 'https://bizapi.csdn.net/blog-console-api/v3/image/transfer'

        content_html = etree.HTML(content)
        src_list = content_html.xpath('//img/@src')
        for src in src_list:
            while 1:
                time_stamp = int(time.time() * 1000)
                salt = self.gen_random()
                form_data = {
                    "uuid": f"img-{salt}-{time_stamp}",
                    "url": src
                }
                base_url = "/blog-console-api/v3/image/transfer"
                self.sess.headers = headers_to_dict(self.gen_header(base_url))
                res = self.sess.post(url=upload_url, json=form_data)
                if res.text:
                    r_json = res.json()
                    # 图片在文章中本来就不存在
                    if r_json.get('code') == 400:
                        return markdowncontent, content
                    img_url = r_json.get('data').get('img_url')
                    content = content.replace(src, img_url)
                    markdowncontent = markdowncontent.replace(src, img_url)
                    time.sleep(random.random() * 0.1)
                    break
            # else:
            #     print("请求响应为空：")
            #     print(res.text, res.cookies.get_dict(), res.status_code)
        return markdowncontent, content

    def del_doc(self, art_url: str):
        art_id = art_url.rsplit('/', 1)[1]
        del_url = 'https://bizapi.csdn.net/blog-console-api/v1/article/del'
        base_url = "/blog-console-api/v1/article/del"
        self.sess.headers = headers_to_dict(self.gen_header(base_url))
        form_data = {"article_id": art_id, "deep": "false"}
        res = self.sess.post(del_url, json=form_data)
        if res.text:
            r_json = res.json()
            code = r_json.get('code')
            msg = r_json.get('msg')
            if code == 200 and msg == "success":
                return True
        return False