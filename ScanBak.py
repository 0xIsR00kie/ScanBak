#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time         : 17/1/2022 3:05 下午
# @Author       : 0xIsR00kie
# @File         : ScanBak.py
# @Description  : 备份文件扫描器
# @Version      : 1.2
import time
import sys
import requests
import tldextract
import argparse
from urllib.parse import urlparse, urljoin
from loguru import logger
from multiprocessing import Pool, Lock
import threading
from queue import Queue
import lxml.html.soupparser as soupparser
from Hook.requests import enable_hook

logger.remove()
logger.add(sys.stdout, enqueue=True)

DOMAIN_FORMAT = ("{}", "{}{}", "{}{}{}", "{}.{}", "{}.{}.{}")
FILE_SUFFIXES = ('.7z', '.gz', '.zip', '.rar', '.sql', '.sql~', '.tar.7z', '.tar.xz', '.tar.gz', '.sql.gz', '.sql.zip')
# FILE_SUFFIXES = ('.sql',)
FILENAMS = ('bbs', 'web', 'www', 'forum', 'backup', 'wwwroot')  # 自定义备份文件名
CONTENT_TYPES = (
    "application/zip",  # zip
    "multipart/x-zip",  # zip 非标准
    "application/x-zip-compressed",  # zip 非标准
    "application/gzip",  # tar.gz
    "application/x-rar",  # rar
    "application/x-rar-compressed",  # rar
    "application/sql",  # sql
    "text/sql",  # sql
    "text/x-sql",  # sql
    "text/plain",  # 文本通用
    "application/octet-stream"  # 压缩包通用
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36",
    # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Referer": "",
    "Host": ""
}

parser = argparse.ArgumentParser()
FILE_LOCK = None
FLAGS = None
LOGGER = None
enable_hook()


class SensitivePage(object):
    def __init__(self, a_url, b_url):
        self.a_url = a_url
        self.b_url = b_url

    @staticmethod
    def get_domtree(html):
        dom = soupparser.fromstring(html)
        for child in dom.iter():
            yield child.tag

    def similar_web(self):
        headers = HEADERS.copy()
        headers['Referer'] = self.a_url
        headers['Host'] = urlparse(self.a_url).netloc

        html1 = requests.get(self.a_url, headers=headers, timeout=5).text
        html2 = requests.get(self.b_url, headers=headers, timeout=5).text
        dom_tree1 = ">".join(list(filter(lambda e: isinstance(e, str), list(self.get_domtree(html1)))))
        dom_tree2 = ">".join(list(filter(lambda e: isinstance(e, str), list(self.get_domtree(html2)))))
        c, length = self.lcs(dom_tree1, dom_tree2)
        return 2.0 * length / (len(dom_tree1) + len(dom_tree2))

    # - c : 过程处理矩阵
    # - c[x][y] : the lcs-length(最长公共子序列长度)
    def lcs(self, a, b):
        lena = len(a)
        lenb = len(b)
        c = [[0 for i in range(lenb + 1)] for j in range(lena + 1)]
        for i in range(lena):
            for j in range(lenb):
                if a[i] == b[j]:
                    c[i + 1][j + 1] = c[i][j] + 1
                elif c[i + 1][j] > c[i][j + 1]:
                    c[i + 1][j + 1] = c[i + 1][j]
                else:
                    c[i + 1][j + 1] = c[i][j + 1]
        return c, c[lena][lenb]


def run_time(func):
    def wrapper(url, *args, **kwargs):
        start = time.time()
        r = func(url, *args, **kwargs)
        LOGGER.info("请求完成 %s 耗时%0.2fs" % (url, (time.time() - start)))
        return r

    return wrapper


@run_time
def get_request(url: str, *args, **kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = FLAGS.timeout

    if FLAGS.is_head:
        return requests.head(url, *args, **kwargs)
    else:
        if 'stream' not in kwargs:
            kwargs['stream'] = True
        return requests.get(url, *args, **kwargs)


def format_domain(domain: str) -> ():
    result = []
    tld = tldextract.extract(domain)
    for i in DOMAIN_FORMAT:
        if i == "{}":
            result.append(i.format(tld.domain))
        elif len(tld.subdomain) == 0 or (i == "{}{}" or i == "{}.{}"):
            try:
                result.append(i.format(tld.domain, tld.suffix))
            except IndexError:
                continue
        else:
            if tld.subdomain.find('.') > 0:
                if i == "{}{}{}":
                    result.append(i.format(tld.subdomain.replace('.', ''), tld.domain, tld.suffix))
                    continue
            result.append(i.format(tld.subdomain, tld.domain, tld.suffix))
    return tuple(result)


def domain_bak_scanner(url: str, path: str) -> bool:
    result = False
    headers = HEADERS.copy()
    headers['Referer'] = url
    headers['Host'] = urlparse(url).netloc
    task = urljoin(url, path)
    try:
        r = get_request(task, headers=headers)
    except Exception as err:
        LOGGER.warning(err)
        return result

    if r.status_code != 200:
        LOGGER.debug("[-] %s [%d]" % (task, r.status_code))
        r.close()
        return result

    if r.headers.get('Content-Type') in CONTENT_TYPES:
        length = int(r.headers.get("Content-Length", 0))
        if length >= (1024 * 1024 * FLAGS.file_size):  # 大文件不进行相识度识别 5MB
            LOGGER.success(
                "[+] 大文件 %s [%d] %s [%s]" % (task, r.status_code, r.headers.get('content-type', None), length))
            result = True
            r.close()
            return result

        randomurl = urljoin(url, '/sdgsdfsd404.php')
        percent = SensitivePage(task, randomurl)
        similar_result = 0
        try:
            similar_result = percent.similar_web()
        except Exception as err:
            logger.error(err)

        if similar_result != float(1):
            if '<html' in r.text or r.text.endswith('</html>'):
                logger.warning('[-] 结果包含 %s [<html or </html>] 跳过' % (task,))
                r.close()
                return result
            LOGGER.success("[+] %s [%d] %s [%s]" % (task, r.status_code, r.headers.get('content-type', 0), length))
            result = True
            r.close()
            return result
        else:
            LOGGER.warning("[-] 404页面 %s [%d]" % (task, r.status_code))
            r.close()
            return result


def _run_thread(queue: Queue, lock: threading.Lock):
    time.sleep(1)
    while not queue.empty():
        try:
            task = queue.get(timeout=1)
        except Exception:
            continue
        with lock:
            if domain_bak_scanner(*task):
                with FILE_LOCK:
                    with open(FLAGS.output, 'a', encoding='utf-8') as f:
                        f.write(urljoin(*task) + '\n')
                while not queue.empty():
                    task = queue.get(timeout=0.1)


def _work_process(url: str):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    headers = HEADERS.copy()
    headers['Referer'] = url
    headers['Host'] = urlparse(url).netloc
    try:
        r = get_request(url, headers=headers, allow_redirects=True)
        p = urlparse(r.url)
        url = "%s://%s" % (p.scheme, p.netloc)
    except Exception as err:
        LOGGER.warning("[-] 请求异常: %s %s 跳过" % (url, err))
        return

    queue = Queue()
    tasks = format_domain(urlparse(url).netloc)
    LOGGER.info("[+] %s 任务开始" % url)
    for s in FILE_SUFFIXES:
        for task in tasks:
            queue.put((url, task + s))
        for ss in FILENAMS:
            queue.put((url, ss + s))
    lock = threading.Lock()
    ts = [threading.Thread(target=_run_thread, args=(queue, lock)) for _ in range(FLAGS.thread)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    LOGGER.info("[+] %s 任务结束" % url)


def initialize(l, f, log):
    global FILE_LOCK, FLAGS, LOGGER
    FILE_LOCK = l
    FLAGS = f
    LOGGER = log


if __name__ == "__main__":
    parser.add_argument('-u', '--url', type=str, help='扫描单个目标')
    parser.add_argument('-f', '--file', type=str, help='批量扫描')
    parser.add_argument('-p', '--processes', type=int, default=10, help='进程数. 同时处理多少域名. 默认10')
    parser.add_argument('-t', '--thread', type=int, default=5, help='内部线程.每个域名同时处理多少检查. 默认5')
    parser.add_argument('-o', '--output', type=str, default='output.txt', help='输出结果文件')
    parser.add_argument('--timeout', type=int, default=10, help='连接超时 默认: 10s')
    parser.add_argument('--file-size', type=int, default=2, help='文件大小, 超过将不进行误报识别: 2m')
    parser.add_argument('--is-head', type=bool, nargs='?', const=True, default=False, help='开启高速模式')
    f, unparsed = parser.parse_known_args()

    if f.url:
        initialize(Lock(), f, logger)
        _work_process(f.url)
    elif f.file:
        with open(f.file, 'r', encoding='utf8') as _f:
            lines = []
            for line in _f:
                if line.strip() in lines:
                    logger.warning("重复任务: %s 跳过" % line)
                    continue
                try:
                    lines.append(line.strip())
                except UnicodeDecodeError:
                    logger.error("[-] 读取文件错误: %s" % line)
        pool = Pool(processes=f.processes, initializer=initialize, initargs=(Lock(), f, logger))
        pool.map(_work_process, lines)
        pool.close()
        pool.join()
    else:
        parser.print_help()
