# -*-coding:utf-8-*-
import lxml.html.soupparser as soupparser
import requests
import argparse
from queue import Queue
import threading
import sys
import time
from urllib import parse
import tldextract
from loguru import logger

lock = threading.Lock()

tasks = Queue(1000)
parser = argparse.ArgumentParser()

headers = {
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
}

zips = ('.sql', '.zip', '.7z', '.rar', '.gz', '.tar.gz', '.bz2', '.tar')


class sensitivepage(object):
    def __init__(self, a_url, b_url):
        self.a_url = a_url
        self.b_url = b_url

    @staticmethod
    def get_domtree(html):
        dom = soupparser.fromstring(html)
        for child in dom.iter():
            yield child.tag

    def similar_web(self):
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


def add_task():
    with open(FLAGS.suffix, 'r', encoding='utf8') as _suffix:
        suffixs = [line.strip() for line in _suffix.readlines()]

    logger.debug(FLAGS.file)
    with open(FLAGS.file, 'r', encoding='utf8') as _file:
        # line = _file.readline()
        # while line:
        for line in _file.readlines():
            items = []
            line = line.strip()
            if not (line.startswith('http://') or line.startswith('https://')):
                line = 'http://' + line
            tld = tldextract.extract(parse.urlparse(line).netloc)
            items.append(tld.domain)  # baidu
            items.append("%s.%s" % (tld.domain, tld.suffix))  # baidu.com
            items.append("%s.%s.%s" % (tld.subdomain, tld.domain, tld.suffix))  # www.baidu.com
            items.append("%s%s" % (tld.domain, tld.suffix))  # baiducom
            items.append("%s%s%s" % (tld.subdomain, tld.domain, tld.suffix))  # wwwbaiducom
            for item in items:
                for s in zips:
                    tasks.put(parse.urljoin(line, item + s))

            for suffix in suffixs:
                for s in ['1', '.1', '_old', '.tmp', '.log', '.bak', '.txt', '_bak', '-bak', '.old', '.new']:
                    tasks.put(line + suffix + s)


def work_in():
    time.sleep(0.3)
    while not tasks.empty():
        try:
            task = tasks.get(timeout=1)
        except Exception:
            continue

        try:
            res = requests.get(task, timeout=10, headers=headers)
        except Exception:
            continue

        parse_result = parse.urlparse(task)
        scheme, domain = parse_result.scheme, parse_result.netloc
        randomurl = scheme + '://' + domain + '/fewfwf34.php'
        percent = sensitivepage(task, randomurl)
        try:
            result = percent.similar_web()
        except Exception as err:
            logger.error(err)
            result = 0

        # logger.debug("%s, %s, %s" % (res.status_code, result, task))
        is_write = False
        if task.endswith(zips) and res.status_code == 200 and result != float(1):
            if '<html>' in res.text or res.text.endswith('</html>'):
                logger.debug('[-] %s' % (task))
                continue
            is_write = True
        elif res.status_code == 200 and "define" in res.text and result != float(1):
            if '<html>' in res.text or res.text.endswith('</html>'):
                logger.debug('[-] %s' % (task))
                continue
            is_write = True
        else:
            logger.debug('[-] %s' % (task))

        if is_write:
            with lock:
                with open(FLAGS.output, 'a', encoding='utf-8') as f:
                    f.write(task + '\n')
                logger.info('[+] %s' % (task))


if __name__ == "__main__":
    parser.add_argument('-u', '--url', type=str, help='扫描单个目标')
    parser.add_argument('-f', '--file', type=str, help='批量扫描')
    parser.add_argument('-t', '--thread', type=int, default=50, help='线程数. 默认20')
    parser.add_argument('-s', '--suffix', type=str, default='suffix.txt', help='后缀文件')
    parser.add_argument('-o', '--output', type=str, default='output.txt', help='输出结果文件')
    FLAGS, unparsed = parser.parse_known_args()

    if len(sys.argv) < 2:
        parser.print_help()
        exit()

    threading.Thread(target=add_task).start()

    thds = [threading.Thread(target=work_in) for _ in range(FLAGS.thread)]
    [thd.start() for thd in thds]
    [thd.join() for thd in thds]
