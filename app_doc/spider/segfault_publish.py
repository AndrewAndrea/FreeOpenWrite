# -*- coding: utf-8 -*-
# @Time : 2021/2/4 17:22
# @Author : zj
# @File : segfault_publish.py
# @Project : spider_publish
import requests

from app_doc.spider.utils.tools import headers_to_dict


class SegFaultPublish:
    def __init__(self, seg_token):
        self.sess = requests.session()
        base_header = f"""
            accept: */*
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9
            content-type: application/json
            cookie: 123
            token: {seg_token}
            origin: https://segmentfault.com
            referer: https://segmentfault.com/
            user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36
            
        """
        self.sess.headers = headers_to_dict(base_header)

    def get_tags(self, tags):
        new_tags = []
        for i in tags.split(','):
            url = f'https://gateway.segmentfault.com/tags?query=search&q={i}'
            res = self.sess.get(url)
            if res.text:
                r_json = res.json()
                rows = r_json.get('rows')
                name = rows[0].get('name')
                tag_id = rows[0].get('id')
                new_tags.append(tag_id)
        return new_tags

    def get_draft_id(self, mdcontent, tags, title):
        # 获取 draft_id
        url = 'https://gateway.segmentfault.com/draft'
        form_data = {"title": title,
                     "tags": [tags],
                     "text": mdcontent,
                     "object_id": "",
                     "type": "article"}
        res = self.sess.post(url, json=form_data)
        if "Unauthorized" in res.text:
            return "need_login"
        if res.text:
            r_json = res.json()
            draft_id = r_json.get('id')
            return draft_id
        return

    def publish_content(self, tags, markdowncontent, title):
        draft_id = self.get_draft_id(markdowncontent, tags, title)
        if draft_id == 'need_login':
            return draft_id
        if not draft_id:
            return None
        new_tags = self.get_tags(tags)
        url = 'https://gateway.segmentfault.com/article'
        form_data = {
            "tags": new_tags,
            "title": title,
            "text": markdowncontent,
            "draft_id": draft_id,
            "blog_id": "0",
            "type": 1,
            "url": "",
            "cover": "",
            "license": 1,
            "log": ""
        }
        # 成功的状态码为 201，只需要token 即可
        res = self.sess.post(url=url, json=form_data)
        if res.text:
            return res.text
        return None

    def del_doc(self, art_url, reason=None):
        art_id = art_url.rsplit('/', 1)[1]
        form_data = {"reason": "推广广告信息", "other": ""}
        del_url = f'https://gateway.segmentfault.com/article/{art_id}'
        res = self.sess.delete(del_url, json=form_data)
        if res.status_code == 204:
            return True
        return False
