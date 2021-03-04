# -*- coding: utf-8 -*-
# @Time : 2020/7/28 14:33
# @Author : zj
# @File : tools.py
# @Project : work_code
import requests


def cookie_to_dict(cookies):
    row_cookie = cookies.split(';')
    row_dict = dict()
    for i in row_cookie:
        if i == '':
            continue
        row = i.strip().split('=', 1)
        row_dict[row[0].strip()] = row[1].strip()
    return row_dict


def headers_to_dict(headers):
    row_headear = headers.split('\n')
    row_dict = dict()
    for i in row_headear:
        if i == '':
            continue
        row = i.strip().split(':', 1)
        if len(row) == 0:
            continue
        if row[0] == '':
            continue
        row_dict[row[0].strip()] = row[1].strip()
    return row_dict

