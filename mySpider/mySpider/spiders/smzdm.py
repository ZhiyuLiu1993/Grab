# -*- coding: utf-8 -*-
import os
import sys

import scrapy
from scrapy.http import Request
from scrapy.selector import Selector
import requests
import time


fpath = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
ffpath = os.path.abspath(os.path.join(fpath,".."))
# print(ffpath)
sys.path.append(ffpath)
from mySpider.items import MyspiderItem

class SmzdmSpider(scrapy.Spider):
    name = 'smzdm'
    allowed_domains = ['smzdm.com']
    start_urls = ['https://post.smzdm.com/shaiwu/p']
    bashurl = '/'

    params = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        , 'Connection': 'keep-alive'
        , 'Pragma': 'no-cache'
        , 'Cache-Control': 'no-cache'
        #    ,'Upgrade-Insecure-Requests': "1"
        , 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        , 'Accept-Encoding': 'gzip, deflate, br'
        , 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,zh-TW;q=0.6'
    }

    def requests_get_text(sele, url, retrys=3, params=params, headers=headers):
        for i in range(0, retrys):
            try:
                r = requests.get(url, params=params, headers=headers)
                r.encoding = 'utf-8'
                if not r.ok:
                    print(r)
                    continue

                return r.text
            except requests.exceptions.ConnectionError:
                print(url, str(i), "Connection refused")
                time.sleep(5)
            except Exception as err:
                print(url, str(i), err)
                time.sleep(5)

        return ''

    def start_requests(self):
        for i in range(1, 3):
            url = self.start_urls[0] + str(i) + self.bashurl
            print(url)
            yield Request(url, self.parse)

    def parse(self, response):
        index_html = response.text

        # items = []
        for content_url in Selector(text=index_html).xpath('//div[@class="list post-list"]'):
            # print(content_url)
            item = MyspiderItem()
            item["source_url"] = content_url.xpath('div/a/@href').extract()
            item["title"] = content_url.xpath('div/div/h2[@class="item-name"]/a/text()').extract()
            # print(item["title"])

            # items.append(item)
            # sub_html = self.requests_get_text(item["source_url"][0])
            yield Request(str(item["source_url"][0]), meta={'item': item}, callback=self.get_url_content)
        # return items
        # pass

    def get_url_content(self, response):
        # print("#############################")
        item = response.meta['item']

        return item




