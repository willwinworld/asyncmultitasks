#! python2
# -*- coding:utf-8 -*-


import time
from datetime import timedelta

try:
    from HTMLParser import HTMLParser
    from urlparse import urljoin, urldefrag
except ImportError:
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urldefrag

from tornado import httpclient, gen, ioloop, queues

base_url = 'https://movie.douban.com/top250'
concurrency = 10


@gen.coroutine
def get_links_from_url(url):  # 获取传入url里的链接
    """Download the page at `url` and parse it for links.

    Returned links have had the fragment after `#` removed, and have been made
    absolute so, e.g. the URL 'gen.html#tornado.gen.coroutine' becomes
    'http://www.tornadoweb.org/en/stable/gen.html'.
    """
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(url)  # 异步抓取url,获得url的响应
        print('fetched %s' % url)

        html = response.body if isinstance(response.body, str) \
            else response.body.decode()  # 获取响应的文本内容
        urls = [urljoin(url, remove_fragment(new_url))
                for new_url in get_links(html)]  # 将相对url转换为绝对url
    except Exception as e:
        print('Exception: %s %s' % (e, url))
        raise gen.Return([])  # Special exception to return a value from a coroutine.

    raise gen.Return(urls)  # If this exception is raised, its value argument is used as the result of the coroutine.


def remove_fragment(url):
    pure_url, frag = urldefrag(url)  # 去除#号
    return pure_url


def get_links(html):  # 从文本中提取链接
    class URLSeeker(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)  # 继承 等价于super.__init__(self)
            self.urls = []

        def handle_starttag(self, tag, attrs):
            href = dict(attrs).get('href')
            if href and tag == 'a':
                self.urls.append(href)

    url_seeker = URLSeeker()
    url_seeker.feed(html)
    print('@@'*20)
    print(url_seeker.urls)
    print('@@'*20)
    return url_seeker.urls  # 找到链接里的子链接


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
            urls = yield get_links_from_url(current_url)  # 获取current_url里的响应
            fetched.add(current_url)

            for new_url in urls:
                # Only follow links beneath the base URL
                if new_url.startswith(base_url):
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






