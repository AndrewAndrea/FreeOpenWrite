# -*- coding: utf-8 -*-
# @Time : 2021/2/4 17:22
# @Author : zj
# @File : juejin_publish.py
# @Project : spider_publish
import requests

from app_doc.spider.utils.tools import headers_to_dict


class JueJinPublish:
    def __init__(self, cookie):
        self.sess = requests.session()
        base_header = f"""
            accept: */*
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9
            content-type: application/json
            cookie: {cookie}
            origin: https://juejin.cn
            referer: https://juejin.cn/
            user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36
        """
        self.sess.headers = headers_to_dict(base_header)

    def get_tags(self, tags):
        new_tags = []
        for i in tags.split(','):
            form_data = {
                "key_word": i
            }
            url = f'https://api.juejin.cn/tag_api/v1/query_tag_list'
            res = self.sess.post(url, json=form_data)
            # print(res.text)
            if res.text:
                r_json = res.json()
                data = r_json.get('data')
                if data:
                    new_tags.append(data[0].get('tag_id'))
                    return new_tags

    def get_category(self):
        # 获取 draft_id
        url = 'https://api.juejin.cn/tag_api/v1/query_category_list'
        form_data = {}
        res = self.sess.post(url, json=form_data)
        if res.text:
            r_json = res.json().get('data')
            return r_json
        return None

    def publish_content(self, tags, markdowncontent, title, plant_config):
        if not plant_config:
            return False
        if tags:
            tags = self.get_tags(tags=tags)
        else:
            tags = self.get_tags(tags=plant_config[0].tags)
        form_data = {
                     "category_id": "0",
                     "tag_ids": [],
                     "link_url": "",
                     "cover_image": "",
                     "title": title,
                     # 简介 标题 100个字符
                     "brief_content": "",
                     "edit_type": 10,
                     "html_content": "deprecated",
                     "mark_content": ""}
        create_url = 'https://api.juejin.cn/content_api/v1/article_draft/create'
        create_res = self.sess.post(url=create_url, json=form_data)
        if create_res.json().get('err_no') == 0:
            art_id = create_res.json().get('data').get('id')
            user_id = create_res.json().get('data').get('user_id')

            # 实时保存接口，文章被保存为草稿
            url = 'https://api.juejin.cn/content_api/v1/article_draft/update'
            form_data.update({'id': art_id, 'mark_content': markdowncontent, 'tag_ids': tags,
                              'category_id': plant_config[0].category_value})
            update_res = self.sess.post(url, json=form_data)
            publish_url = 'https://api.juejin.cn/content_api/v1/article/publish'
            pub_form_data = {"draft_id": art_id, "sync_to_org": False}
            publish_res = self.sess.post(publish_url, json=pub_form_data)
            if publish_res.status_code == 200:
                return publish_res.text
        return False

    def del_doc(self, art_url):
        art_id = art_url.rsplit('/', 1)[1]
        form_data = {
            "article_id": art_id
        }
        del_url = 'https://api.juejin.cn/content_api/v1/article/delete'
        res = self.sess.post(del_url, json=form_data)
        if res.status_code == 200:
            return True
        return False
