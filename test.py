#! python3
# -*- coding: utf-8 -*-
import re
import requests
# from dateutil.parser import parse
from pyquery import PyQuery as pq
#
#
# url = 'http://www.spp.gov.cn/gjyjg/zssydw/201208/t20120816_908.shtml'
# r = requests.get(url)
# d = pq(r.text).make_links_absolute(base_url=url)
# content_node = d('.bor_4')
# pic = []
# for node in content_node:
#     dollar = pq(node).make_links_absolute(base_url=url)
#     if dollar('.wzbt'):
#         title = dollar('.wzbt').text()
#     else:
#         title = ''
#     if dollar('#pubtime_baidu'):
#         article_time = parse(dollar('#pubtime_baidu').text(), fuzzy=True)
#     else:
#         article_time = ''
#     if dollar('#author_baidu'):
#         author = dollar('#author_baidu').text().split(u'：')[-1]
#     else:
#         author = ''
#     if dollar('#source_baidu'):
#         source = dollar('#source_baidu').text().split(u'：')[-1]
#     else:
#         source = ''
#     if dollar('#fontzoom p'):
#         content = dollar('#fontzoom p').text()
#     else:
#         content = ''
#     if dollar('img').attr('src'):
#         img = dollar('img').attr('src')
#         pic.append(img)
#     else:
#         pic = []
#     res = {'title': title, 'time': str(article_time), 'author': author,
#            'source': source,
#            'content': content, 'img': pic, 'url': url}
# print(res)
# urls =[]
# base_url = 'https://movie.douban.com/top250'
# r = requests.get(base_url)
# d = pq(r.text).make_links_absolute(base_url=base_url)
# paginator_node = d('.paginator a')
# paginator_urls = [d(node).attr('href') for node in paginator_node]
# print(paginator_urls)
# film_node = d('.grid_view .info a')
# links = [d(node).attr('href') for node in film_node]
# print(links)
# print(film_node)
# for node in film_node:
#     dollar = pq(node)
#     film_url = dollar('.info a').attr('href')
#     urls.append(film_url)
# print(urls)

# url = 'https://movie.douban.com/subject/1291552/'
# num = re.findall(r'\d+', url)
# print(num)

# base_url = 'http://www.spp.gov.cn/'
# r = requests.get(base_url)
# d = pq(r.text).make_links_absolute(base_url=base_url)
# nodes = d('body a')
# urls = set(d(node).attr('href') for node in nodes)
# print(urls)
# kkk = []
# link = d('body a')
# for item in link.items():
#     if item.attr('href'):
#         url = item.attr('href')
#         kkk.append(url)
# print('@@'*20)
# print(kkk)
import string
import re
from operator import is_not
from functools import partial
# urls = ['http:www.baidu.com', 'http:www.google.com', '123', None]
# l = filter(partial(is_not, None), urls)
# print(l)
# links = [url for url in l if url.startswith('http')]
# print(links)
base_url = 'http://www.spp.gov.cn/'
urls = ['http://www.baidu.com', 'http://www.google.com', '123', 'http://60.123', 'http://abc',
        'http://www.spp.gov.cn/gzbg/200602/t20060222_16375.shtml', None, 'http://www.spp.gov.cn/gzbg/200602/t20060222_16375']
non_none = filter(partial(is_not, None), urls)
links = [url for url in non_none if url.startswith(base_url) and url.endswith('.shtml')]
print(links)


