#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time         : 2021/10/1 18:51
# @Author       : 0xIsRookie
# @File         : requests.py
# @Description  : requests 请求参数注入
# @Version      : 1.0

import re
import requests
import urllib3
from loguru import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # 关闭证书未效验警告
requests_get = requests.get
requests_post = requests.post
requests_put = requests.put
requests_delete = requests.delete


@logger.catch
def requests_inject_args(func):
    def wrapper(url, *args, **kwargs):
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        if "timeout" not in kwargs:
            kwargs["timeout"] = 30
        if "allow_redirects" not in kwargs:  # 关闭301自动重定向
            kwargs["allow_redirects"] = False
        if "verify" not in kwargs:  # 默认关闭ssl效验
            kwargs["verify"] = False
        r = func(url, *args, **kwargs)
        if r:
            # 匹配请求头中的编码信息
            try:
                headers_encoding = re.findall(r'charset=[\'"]?([\S\d-]*)[\'"]?', r.headers.get('Content-Type'), re.I)[0]
            except IndexError:
                headers_encoding = r.apparent_encoding

            # 匹配页面中的编码信息
            html = r.text
            try:
                html_encoding = re.findall(r'charset=[\'"]?([\S\d-]*)[\'"]?', html, re.I)[0].rstrip('"')
            except IndexError:
                html_encoding = r.apparent_encoding
            try:
                if headers_encoding == html_encoding:
                    r.encoding = headers_encoding
                else:
                    r.encoding = html_encoding
            except Exception as err:
                logger.error(err)
                r.encoding = r.apparent_encoding
        return r

    return wrapper


@requests_inject_args
def my_get(url, *args, **kwargs):
    return requests_get(url, *args, **kwargs)


@requests_inject_args
def my_post(url, *args, **kwargs):
    return requests_post(url, *args, **kwargs)


@requests_inject_args
def my_put(url, *args, **kwargs):
    return requests_put(url, *args, **kwargs)


@requests_inject_args
def my_delete(url, *args, **kwargs):
    return requests_delete(url, *args, **kwargs)


def enable_hook():
    # if requests.get != my_get:
    #     logger.info("requests Hook UP")
    requests.get = my_get
    requests.post = my_post
    requests.put = my_put
    requests.delete = my_delete


def disabled_hook():
    requests.get = requests_get
    requests.post = requests_post
    requests.put = requests_put
    requests.delete = requests_delete
