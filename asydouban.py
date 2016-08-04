#! python2
# -*- coding:utf-8 -*-
import re
import json
import time
from datetime import timedelta
from pyquery import PyQuery as pq
from tornado import httpclient, gen, ioloop, queues


base_url = 'https://movie.douban.com/top250'
concurrency = 10


def save(url, html):
    filename = re.findall(r'\d+', url)[0]
    res = parse(url, html)
    standard_output = json.dumps(res, sort_keys=True, indent=4).decode('unicode-escape').encode('utf8')
    with open('html/%s.json' % filename, 'w') as f:
        f.write(standard_output)


def parse(url, html):
    d = pq(html)
    title = d('h1 span[property]').text()
    rate = d('.ll.rating_num').text()
    summary = d('#link-report span[property]').text()
    rank = d('.top250 .top250-no').text()
    res = {'url': url, 'title': title, 'rate': rate, 'summary': summary, 'rank': rank}
    return res


@gen.coroutine
def get_links_from_url(url):
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(url)
        html = response.body
        urls = get_links(html)
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


def get_links(html):
    d = pq(html).make_links_absolute(base_url=base_url)
    film_node = d('.grid_view .info a')
    film_urls = [d(node).attr('href') for node in film_node]
    paginator_node = d('.paginator a:lt(9)')
    paginator_urls = [d(node).attr('href') for node in paginator_node]
    urls = film_urls + paginator_urls
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
    yield q.join(timeout=timedelta(seconds=300))
    assert fetching == fetched
    print('Done in %d seconds, fetched %s URLs.' % (
        time.time() - start, len(fetched)))


if __name__ == '__main__':
    import logging
    logging.basicConfig()
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)



