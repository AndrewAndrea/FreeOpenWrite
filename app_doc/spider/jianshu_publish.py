# -*- coding: utf-8 -*-
# @Time : 2021/4/1 16:37
# @Author : zj
# @File : jianshu_publish.py
# @Project : spider_publish
import random
import time

import markdown
import requests
import arrow

from lxml import etree
from requests_toolbelt import MultipartEncoder
from app_doc.spider.utils.tools import headers_to_dict


class JianShuPublish:
    def __init__(self, cookie):
        """
        @param cookie:
        """
        self.sess = requests.session()
        base_header = f"""
            Accept: application/json
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            Cookie: {cookie}
            Host: www.jianshu.com
            Origin: https://www.jianshu.com
            Referer: https://www.jianshu.com/writer
            User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36       
        """
        self.sess.headers = headers_to_dict(base_header)

    # 获取文集列表
    def get_notebooks(self):
        url = 'https://www.jianshu.com/author/notebooks'
        res = self.sess.get(url)
        if res.text:
            return res.json()
        return False

    # 新建文集
    def add_notebooks(self, name):
        url = 'https://www.jianshu.com/author/notebooks'
        res = self.sess.post(url, json={"name": name})
        print(res.text)
        if res.text:
            return res.json()
        return False

    # 创建新文章，返回note_id
    def create_new_notes(self, notebook_id):
        title = arrow.now().date()
        url = 'https://www.jianshu.com/author/notes'
        form_data = {"notebook_id": notebook_id, "title": str(title), "at_bottom": True}
        res = self.sess.post(url, json=form_data)
        if res.text:
            return res.json()
        return False

    def upload_img(self, content):
        upload_head = """
            accept: application/json
            accept-language: zh-CN,zh;q=0.9
            origin: https://www.jianshu.com
            referer: https://www.jianshu.com/
            user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36
        """
        upload_url = 'https://upload.qiniup.com/'
        md = markdown.Markdown(extensions=['markdown.extensions.extra', 'markdown.extensions.codehilite'])
        content_html = md.convert(content)
        res_html = etree.HTML(content_html)
        src_list = res_html.xpath('//img/@src')
        for src in src_list:
            res_img = requests.get(src)
            file_name = src.rsplit('/', 1)[1].rsplit('.')[0] + '.png'
            token_url = f'https://www.jianshu.com/upload_images/token.json?filename={file_name}'
            res_token = self.sess.get(token_url)
            if res_token.text:
                res_token_json = res_token.json()
                token = res_token_json.get('token')
                key = res_token_json.get('key')
                if token and key:
                    m = MultipartEncoder(
                        fields={"file": (file_name, res_img.content),
                                'token': token, 'key': key, 'x:protocol': 'https'})
                    headers_dict = headers_to_dict(upload_head)
                    headers_dict['Content-Type'] = m.content_type

                    res_upload_file = requests.post(url=upload_url, data=m, headers=headers_dict)
                    if res_upload_file.text:
                        r_json = res_upload_file.json()
                        if r_json.get('error'):
                            continue
                        # 图片在文章中本来就不存在
                        img_url = r_json.get('url')
                        content = content.replace(src, img_url)
                        time.sleep(random.random())
        return content

    # 文章保存
    def save_note(self, note_id, title, content):
        content = self.upload_img(content)
        url = f'https://www.jianshu.com/author/notes/{note_id}'
        form_data = {"id": note_id, "autosave_control": 4, "title": title, "content": content}
        res = self.sess.put(url, json=form_data)
        if res.text:
            return res.text
        return False

    def publish_content(self, tags, markdowncontent, title, plant_config):
        if plant_config[0].category_value:
            json_res = self.create_new_notes(notebook_id=plant_config[0].category_value)
            edit_id = json_res.get('id')
            push_id = json_res.get('slug')
        else:
            return False
        res_str = self.save_note(edit_id, title=title, content=markdowncontent)
        if res_str:
            url = f'https://www.jianshu.com/author/notes/{edit_id}/publicize'
            res = self.sess.post(url=url, json={})
            if res.text:
                if res.json().get('error'):
                    return res.json()
                return json_res
        return False

    def del_doc(self, art_url, reason=None):
        edit_id = art_url.rsplit('?', 1)[1]
        del_url = f'https://www.jianshu.com/author/notes/{edit_id}/soft_destroy'
        res = self.sess.post(del_url)
        if res.status_code == 200:
            return True
        return False
