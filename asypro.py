#! python2
# -*- coding:utf-8 -*-
import re
import json
import time
import requests
from datetime import timedelta
from dateutil.parser import parse
from pyquery import PyQuery as pq
from tornado import httpclient, gen, ioloop, queues


base_url = 'http://www.spp.gov.cn/'
concurrency = 10


def save(url, html):
    judge = check(url, html)
    if judge:
        res = analyze(url, html)
        standard_output = json.dumps(res, sort_keys=True, indent=4).decode('unicode-escape').encode('utf8')
        filename = re.findall(r't(\d+_\d+)', url)
        if not filename == []:
            text = res['title'].replace('\\', '').replace('/', '').replace(':', '').replace('*', '') \
                .replace('?', '').replace('"', '').replace('>', '').replace('<', '').replace('|', '')
            with open('success/spp_%s_%s.json' % (filename[0], text), 'w') as f:
                f.write(standard_output)


def check(url, html):
    if url.startswith(base_url):
        element = 'bor_4'
        if url.endswith('.shtml') and element in html:
            return True
        else:
            return False


def analyze(url, html):
    d = pq(html).make_links_absolute(base_url=url)
    article_node = d('.bor_4')
    pic = []
    for node in article_node:
        dollar = pq(node)
        if dollar('.wzbt'):
            title = dollar('.wzbt').text()
        else:
            title = ''
        if dollar('#pubtime_baidu'):
            article_time = parse(dollar('#pubtime_baidu').text(), fuzzy=True)
        else:
            article_time = ''
        if dollar('#author_baidu'):
            author = dollar('#author_baidu').text().split(u'：')[-1]
        else:
            author = ''
        if dollar('#source_baidu'):
            source = dollar('#source_baidu').text().split(u'：')[-1]
        else:
            source = ''
        if dollar('#fontzoom p'):
            content = dollar('#fontzoom p').text()
        else:
            content = ''
        if dollar('img').attr('src'):
            img = dollar('img').attr('src')
            pic.append(img)
        else:
            pic = []
        res = {'title': title, 'time': str(article_time), 'author': author,
               'source': source,
               'content': content, 'img': pic, 'url': url}
        return res


@gen.coroutine
def get_links_from_url(url):
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(url)
        html = response.body
        urls = get_links(url, html)
    except Exception as e:
        print('Exception: %s %s' % (e, url))
        raise gen.Return([])

    raise gen.Return(urls)


@gen.coroutine
def get_page(url):
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(url)
    except Exception as e:
        print('Exception: %s %s' % (e, url))
        raise gen.Return('')
    raise gen.Return(response.body)


def get_links(url, html):  # 获得页面的所有链接
    d = pq(html).make_links_absolute(base_url=url)
    key_node = d('body a')
    urls = set(d(node).attr('href') for node in key_node)
    return urls


@gen.coroutine
def main():
    q = queues.Queue()
    start = time.time()
    fetching, fetched = set(), set()

    @gen.coroutine
    def fetch_url():
        current_url = yield q.get()
        try:
            if current_url in fetching:
                return

            print('fetching %s' % current_url)
            fetching.add(current_url)
            html = yield get_page(current_url)
            urls = yield get_links_from_url(current_url)  # 获取current_url里的响应
            fetched.add(current_url)

            save(current_url, html)

            for new_url in urls:
                yield q.put(new_url)  # 将新的链接又放入队列中

        finally:
            q.task_done()

    @gen.coroutine
    def worker():
        while True:
            yield fetch_url()  # 多协程

    q.put(base_url)

    # Start workers, then wait for the work queue to be empty.
    for _ in range(concurrency):
        worker()
    yield q.join(timeout=timedelta(seconds=300000000))
    assert fetching == fetched
    print('Done in %d seconds, fetched %s URLs.' % (
        time.time() - start, len(fetched)))


if __name__ == '__main__':
    import logging
    logging.basicConfig()
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)



