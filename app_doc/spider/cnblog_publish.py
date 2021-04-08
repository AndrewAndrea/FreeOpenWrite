# -*- coding: utf-8 -*-
# @Time : 2021/2/4 17:22
# @Author : zj
# @File : cnblog_publish.py
# @Project : spider_publish
import os
import requests
import arrow
import hmac
import base64
import execjs
from hashlib import sha256
from app_doc.spider.utils.tools import headers_to_dict, cookie_to_dict


class CNBlogPublish:
    def __init__(self, cookie):
        self.sess = requests.session()
        base_header = f"""
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9
            cookie: {cookie}
            referer: https://i.cnblogs.com/posts/edit
            user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36
        """
        self.sess.headers = headers_to_dict(base_header)
        edit_url = 'https://i.cnblogs.com/posts/edit'
        res_edit = self.sess.get(edit_url)
        self.xsrf_token = res_edit.cookies.get_dict().get('XSRF-TOKEN')

    def get_blog_id(self):
        # 获取 x-blog_id
        url = 'https://i.cnblogs.com/api/user'
        self.sess.headers.update({'accept': 'application/json, text/plain, */*'})
        res = self.sess.get(url)
        if res.text:
            r_json = res.json()
            blogId = r_json.get('blogId')
            return blogId
        return None

    def get_blog_cate(self):
        x_blog_id = self.get_blog_id()
        if x_blog_id:
            # 获取博客分类，获取的是已经存在的分类
            url = 'https://i.cnblogs.com/api/category/blog/1/edit'
            self.sess.headers.update({'x-blog-id': str(x_blog_id)})
            res = self.sess.get(url)
            if res.text:
                return res.json()
        return None

    def publish_content(self, tags, markdowncontent, title, is_markdown, plant_config):

        utc_now = arrow.utcnow()
        date_published = str(utc_now).split('+')[0][:-3] + 'Z'
        # x_blog_id = self.get_blog_id()
        # if x_blog_id:
        #     self.sess.headers.update({'x-blog-id': str(x_blog_id)})
        self.sess.headers.update({'x-xsrf-token': self.xsrf_token})
        url = 'https://i.cnblogs.com/api/posts'
        category_id = None
        if plant_config:
            category_id = plant_config[0].category_value
        if not tags:
            if plant_config:
                tags = plant_config[0].tags
        form_data = {
            "id": None,
            "postType": 1,
            "accessPermission": 0,
            "title": title,
            "url": None,
            "postBody": markdowncontent,
            "categoryIds": [category_id] if category_id else None,
            "inSiteCandidate": False,
            "inSiteHome": False,
            "siteCategoryId": None,
            "blogTeamIds": None,
            "isPublished": True,
            "displayOnHomePage": True,
            "isAllowComments": True,
            "includeInMainSyndication": True,
            "isPinned": False,
            "isOnlyForRegisterUser": False,
            "isUpdateDateAdded": False,
            "entryName": None,
            "description": None,
            "tags": [tag for tag in tags.split(',')] if tags else None,
            "password": None,
            "datePublished": date_published,
            "isMarkdown": is_markdown,
            "isDraft": is_markdown,
            "autoDesc": None,
            "changePostType": False,
            "blogId": 0,
            "author": None,
            "removeScript": False,
            "clientInfo": None,
            "changeCreatedTime": False,
            "canChangeCreatedTime": False
        }
        res = self.sess.post(url=url, json=form_data)
        if res.status_code == 200:
            return res.text
        return None

    def del_doc(self, art_url: str):
        art_id = art_url.rsplit('/', 1)[1].split('.html')[0]
        # x_blog_id = self.get_blog_id()
        # if x_blog_id:
        #     self.sess.headers.update({'x-blog-id': str(x_blog_id)})
        self.sess.headers.update({'x-xsrf-token': self.xsrf_token})
        doc_publish_url = f"https://i.cnblogs.com/api/posts/{art_id}"
        res = self.sess.delete(doc_publish_url)
        if res.status_code == 204:
            return True
        return False