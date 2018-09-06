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


def itheat_main():
    #原始网站： http://www.itheat.com/post
    os.chdir("D:/网页抓取/itheat_data")
    #TODO:  Deduplication(Done)

    count = 0
    file_num = 0
    url_count = 0

    #get titie tid url
    content_url = "http://www.itheat.com"
    base_title_url = "http://www.itheat.com/post/news/"
    page_url = ".html"

    itheat_dup = {}
    if os.path.exists("itheat_dup.json"):
        itheat_dup = json.loads(io.open("itheat_dup.json", 'r', encoding='utf-8').read())

    try:
        for i in range(1, 100):
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
            for brand_tag in html_soup.find("div", class_="news_list").ul.find_all("li"):
                url_count += 1
                if url_count % 300 == 0:
                    file_num += 1
                # print(brand_tag)
                url_zone = brand_tag.find("a", class_="h_e_img");
                # print(url_zone)
                brand_name = url_zone["href"]
                # print(brand_name)
                if brand_name in itheat_dup:
                    continue
                # print(brand_name)
                itheat_dup[brand_name] = {"id": brand_name}

                brandInfos = {}
                brandInfos["source_url"] = content_url + brand_name
                print(brandInfos["source_url"])

                brandInfos["title"] = url_zone["title"]
                # print(brandInfos["title"])

                brandInfos["category"] = "科技"
                # print(brandInfos["category"])

                brandInfos["author_figureurl"] = ""

                sub_html = requests_get_text(brandInfos["source_url"])
                sub_soup = BeautifulSoup(sub_html, "lxml")

                brandInfos["source_html"] = sub_html

                title_zone = sub_soup.find("div", class_="nn_left")
                title_and_time = title_zone.get_text().split("/")
                if len(title_and_time) > 1:
                    brandInfos["author_name"] = title_and_time[0].strip()
                    time_str = title_and_time[1].strip()
                    time_str = time_str + " 00:00:00"
                    time_arr = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    time_stamp = int(time.mktime(time_arr))
                    brandInfos["create_time"] = time_stamp
                else:
                    brandInfos["author_name"] = ""
                    time_str = title_and_time[0].strip()
                    time_str = time_str + " 00:00:00"
                    time_arr = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    time_stamp = int(time.mktime(time_arr))
                    brandInfos["create_time"] = time_stamp


                curnum = 0
                brandInfos["content"] = []
                content_detail_zone = sub_soup.find("div", itemprop="articleBody")
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

                like_num_tag = sub_soup.find("div", class_="zan").find("a").get_text()
                brandInfos["like_num"] = like_num_tag

                try:
                    comment_num_tag = sub_soup.find("h3", class_="_comment-title").get_text()
                    brandInfos["comment_num"] = re.findall(r"\d+", comment_num_tag)
                    com_num = min(int(brandInfos["comment_num"]), 10)
                    print(com_num)
                    brandInfos["comment_list"] = []
                    if com_num > 0:
                        for comment_detail in sub_soup.find("_comment-thread-message"):
                            if com_num == 0:
                                break
                            brandInfos["comment_list"].append(comment_detail.get_text())
                            com_num -= 1

                except Exception as err:
                    brandInfos["comment_num"] = 0
                    brandInfos["comment_list"] = []

                brandInfos["tags"] = []

                # print(brandInfos)
                file_name = "itheat{}.json".format(str(file_num))
                io.open(file_name, "a+", encoding="utf-8").write(
                json.dumps(brandInfos, sort_keys=True, ensure_ascii=False))
                # enter_line = '\r\n'
                # enter_line = enter_line.encode('utf-8')
                io.open(file_name, "a+").write("\n")

                io.open("itheat_dup.json", "w", encoding="utf-8").write(
                    json.dumps(itheat_dup, indent=4, sort_keys=True, ensure_ascii=False))


    except Exception as err:

        print("-" * 60)
        traceback.print_exc(file=sys.stdout)
        print("-" * 60)

    # print(count)


def usage():
    print(sys.argv[0] + ' -g xxxxs')


if __name__ == "__main__":
    itheat_main()