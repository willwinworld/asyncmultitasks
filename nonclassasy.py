#! python2
# -*- coding: utf-8 -*-
import re
import json
import time
import multiprocessing
from datetime import timedelta
from dateutil.parser import parse
from pyquery import PyQuery as pq
from tornado import httpclient, gen, ioloop, queues


base_url = 'http://www.spp.gov.cn/'
concurrency = 10
griddle = set()
res_q = queues.Queue()


@gen.coroutine
def get_links_from_url(url):
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(url)
        # print('fetched %s' % url)

        html = response.body
        urls = get_links(url, html)
    except Exception as e:
        print('Exception: %s %s' % (e, url))
        raise gen.Return([])

    raise gen.Return(urls)


def get_links(link, html):  # 从文本中提取链接
    urls = []
    doc = pq(html).make_links_absolute(base_url=link)
    link_node = doc('body a')
    for item in link_node:
        if item.get('href'):
            url = item.get('href')
            if url not in griddle:
                griddle.add(url)
                if check(url, html):  # 检查符合解析条件
                    analyze(url, html)
                else:
                    urls.append(url)
    return urls


def check(url, html):
    if url.startswith(base_url):
        element = 'bor_4'
        if url.endswith('.shtml') and element in html:
            return True
        else:
            return False


def analyze(url, html):
    doc = pq(html).make_links_absolute(base_url=url)
    article_node = doc('.bor_4')
    pic = []
    for node in article_node:
        dollar = pq(node).make_links_absolute(base_url=url)
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
        yield res


@gen.coroutine
def main():
    seed_q = queues.Queue()
    start = time.time()
    fetching, fetched = set(), set()

    @gen.coroutine
    def fetch_url():
        current_url = yield seed_q.get()
        try:
            if current_url in fetching:
                return

            # print('fetching %s' % current_url)
            fetching.add(current_url)
            urls = yield get_links_from_url(current_url)
            fetched.add(current_url)

            for new_url in urls:
                yield seed_q.put(new_url)

        finally:
            seed_q.task_done()

    @gen.coroutine
    def fetch_res():
        current_res = yield res_q.get()
        try:
            res = dict(current_res)  # 生成器转换为字典
            standard_output = json.dumps(res, sort_keys=True, indent=4).decode('unicode-escape').encode('utf8')
            num = re.findall(r't(\d+_\d+)', res['url'])
            if not num == []:
                text = res['title'].replace('\\', '').replace('/', '').replace(':', '').replace('*', '') \
                    .replace('?', '').replace('"', '').replace('>', '').replace('<', '').replace('|', '')
                with open('logs/spp_%s_%s.json' % (num[0], text), 'w') as f:
                    f.write(standard_output)
        except Exception as e:
            print('saving err: %s' % e)
        finally:
            res_q.task_done()

    @gen.coroutine
    def worker_url():
        while True:
            yield fetch_url()

    seed_q.put(base_url)

    for _ in range(concurrency):
        worker_url()
    yield seed_q.join(timeout=timedelta(seconds=300))
    assert fetching == fetched
    print('Done in %d seconds, fetched %s URLs.' % (
        time.time() - start, len(fetched)))


if __name__ == '__main__':
    import logging
    logging.basicConfig()
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)
