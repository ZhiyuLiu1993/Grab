#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import requests
import sys, traceback
import io
import os
import os.path
import json
import re
import time
# import math
from bs4 import BeautifulSoup
from builtins import str
from functools import reduce
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.request import Request
from urllib.parse import urlencode
from urllib.parse import urlsplit
import lxml
from urllib.parse import parse_qs
import urllib
import getopt

# import zlib


params = {}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
    # 'User-Agent': 'python-requests/2.19.1'
    , 'Connection': 'keep-alive'
    , 'Pragma': 'no-cache'
    , 'Cache-Control': 'no-cache'
    # , 'Upgrade-Insecure-Requests': "1"
    , 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    , 'Accept-Encoding': 'gzip, deflate'   #这个网站需要去掉br，否则乱码
    , 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,zh-TW;q=0.6'
    # , 'Accept-Language': 'q=0.9,en;q=0.8,ja;q=0.6'
    # , 'cookie': 'GPS=1; VISITOR_INFO1_LIVE=qRp7Qlo5n_A; YSC=byQxq_E8eTw'

}


def download(url, user_agent='wswp', proxy=None, num_retries=3):
    # print(url)
    headers = {'User-agent': user_agent}
    request = Request(url, headers=headers)

    opener = urllib.request.build_opener()
    if proxy:
        proxy_params = {urlparse(url).scheme: proxy}
        opener.add_handler(urllib.request.ProxyHandler(proxy_params))
    try:
        html = opener.open(request).read()
    except urllib.request.URLError as e:
        print('Download error')
        print(e.reason)
        html = None
        if num_retries > 0:
            if num_retries > 0:
                if hasattr(e, 'code') and 500 <= e.code < 600:
                    # recursively retry 5xx HTTP errors
                    return download(url, user_agent, proxy, num_retries-1)
    return html


# 下载图片
def download_img(img_url, file_name, replace_force=False):
    try:
        # url 合法性
        u = urlparse(img_url)
        if u.netloc == '':
            raise Exception("bad url:" + img_url)

        if os.path.exists(file_name) and not replace_force: return;

        with open(file_name, 'wb') as handle:
            response = requests.get(img_url, stream=True)
            if not response.ok:
                print(response)
                return

            for block in response.iter_content(1024):
                time.sleep(1)
                if not block:
                    break
                handle.write(block)
    except Exception as err:
        print(err)


def requests_get_text(url, retrys=3, params=params, headers=headers):
    for i in range(0, retrys):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=5)
            r.encoding = 'gb2312'
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


def tgbus_main():
    #原始网站： http://tech.tgbus.com/news/Index.shtml
    os.chdir("D:/网页抓取/tgbus_data")
    #TODO:  Deduplication(Done)

    count = 0
    file_num = 0
    url_count = 0

    #get titie tid url
    # content_url = "http:"
    base_title_url = "http://tech.tgbus.com/news/List_"
    page_url = ".shtml"

    tgbus_dup = {}
    if os.path.exists("tgbus_dup.json"):
        tgbus_dup = json.loads(io.open("tgbus_dup.json", 'r', encoding='utf-8').read())

    try:
        #这个网站的序号最新的表示最大，所以需要更新最开始的序号
        for i in range(1536, 1500, -1):
            url = base_title_url + str(i) + page_url
            # print(url)
            try:
                f_raw_html = requests_get_text(url)
                # print(f_raw_html)
            except Exception as err:
                print("err")
                break
            # print(f_raw_html)
            html_soup = BeautifulSoup(f_raw_html, "lxml")
            # open("youtube.html", "w", encoding='utf-8').write(f_raw_html)
            for brand_tag in html_soup.find_all("dl"):
                url_count += 1
                if url_count % 300 == 0:
                    file_num += 1
                # print(brand_tag)
                url_zone = brand_tag.dt.find("a");
                brand_name = url_zone["href"]
                if brand_name in tgbus_dup:
                    continue
                # print(brand_name)
                tgbus_dup[brand_name] = {"id": brand_name}

                brandInfos = {}
                brandInfos["source_url"] = brand_name
                print(brandInfos["source_url"])

                brandInfos["title"] = brand_tag.dd.a.get_text()
                # print(brandInfos["title"])
                brandInfos["category"] = brand_tag.find("p", class_="info").a.get_text()
                # print(brandInfos["category"])

                brandInfos["author_figureurl"] = ""
                sub_html = requests_get_text(brandInfos["source_url"])
                sub_soup = BeautifulSoup(sub_html, "lxml")

                brandInfos["source_html"] = sub_html

                try:
                    title_zone = sub_soup.find("div", class_="title").p
                except Exception as err:
                    break

                title_span_num = 0
                for title_span in title_zone.find_all("span"):
                    if title_span_num == 0:
                        # print(title_span)
                        brandInfos["author_name"] = title_span.get_text().split("：")[1].strip()
                    elif title_span_num == 1:
                        time_str = title_span.get_text().split("：")[1].strip()
                        time_arr = time.strptime(time_str, "%Y/%m/%d %H:%M:%S")
                        time_stamp = int(time.mktime(time_arr))
                        brandInfos["create_time"] = time_stamp
                    else:
                        break
                    title_span_num += 1

                brandInfos["comment_num"] = 0

                curnum = 0
                brandInfos["content"] = []
                content_detail_zone = sub_soup.find("div", class_="text")
                for content in content_detail_zone.find_all("p"):
                    content_all = {}
                    img_tag_zone = content.find("img")
                    if img_tag_zone:
                        # print(img_tag_zone)
                        content_all["type"] = 2  # image
                        try:
                            content_all["text"] = img_tag_zone["src"]
                        except Exception as err:
                            continue
                    else:
                        content_all["type"] = 3  # text
                        # content_word = content_tag.find("p")
                        # if content_word:
                        content_all["text"] = content.get_text()
                        if content_all["text"] == "":
                            continue
                    brandInfos["content"].append(content_all)

                brandInfos["comment_list"] = []
                brandInfos["like_num"] = 0

                tag_zone = sub_soup.find("div", class_="mark").dd
                brandInfos["tags"] = []
                tag_list = tag_zone.get_text().strip("\r\n\t ").split("，")
                # print(tag_list)
                for tag_detail in tag_list:
                    brandInfos["tags"].append((tag_detail))

                # print(brandInfos)
                file_name = "tgbus{}.json".format(str(file_num))
                io.open(file_name, "a+", encoding="utf-8").write(
                json.dumps(brandInfos, sort_keys=True, ensure_ascii=False))
                # enter_line = '\r\n'
                # enter_line = enter_line.encode('utf-8')
                io.open(file_name, "a+").write("\n")

                io.open("tgbus_dup.json", "w", encoding="utf-8").write(
                    json.dumps(tgbus_dup, indent=4, sort_keys=True, ensure_ascii=False))


    except Exception as err:

        print("-" * 60)
        traceback.print_exc(file=sys.stdout)
        print("-" * 60)

    # print(count)


def usage():
    print(sys.argv[0] + ' -g xxxxs')


if __name__ == "__main__":
    tgbus_main()