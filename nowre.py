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


params = {}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
    # 'User-Agent': 'python-requests/2.19.1'
    , 'Connection': 'keep-alive'
    , 'Pragma': 'no-cache'
    , 'Cache-Control': 'no-cache'
    # , 'Upgrade-Insecure-Requests': "1"
    , 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    , 'Accept-Encoding': 'gzip, deflate, br'
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


def nowre_main():
    #原始网站： http://nowre.com/
    os.chdir("D:/网页抓取/nowre_data")

    #TODO:  Deduplication(Done)

    count = 0
    file_num = 0

    #get titie tid url
    base_title_url = "http://nowre.com/news/page/"

    nowre_dup = {}
    youtube_url = {}
    if os.path.exists("nowre_dup.json"):
        nowre_dup = json.loads(io.open("nowre_dup.json", 'r', encoding='utf-8').read())

    try:
        for i in range(1, 100):
            url = base_title_url + str(i)
            f_raw_html = requests_get_text(url)

            url_count = 0
            html_soup = BeautifulSoup(f_raw_html, "lxml")
            # print(f_raw_html)
            # print(html_soup)
            for brand_tag in html_soup.find_all("div", class_="nowre-list-item"):
                # print(brand_tag)
                url_count += 1
                if url_count % 300 == 0:
                    file_num += 1
                try:
                    brand_name = brand_tag["id"]
                except Exception as err:
                    continue
                if brand_name in nowre_dup:
                    continue
                print(brand_name)
                nowre_dup[brand_name] = {"id": brand_name}

                title_filter_zone = brand_tag.find("a", class_="post-thumbnail nowre-list-item-imgwrap")
                brandInfos = {}
                brandInfos["source_url"] = title_filter_zone["href"]
                brandInfos["title"] = title_filter_zone["title"]

                sub_html = requests_get_text(brandInfos["source_url"])
                sub_soup = BeautifulSoup(sub_html, "lxml")

                brandInfos["source_html"] = sub_html

                name_zone = sub_soup.find("span", class_="term-authors")
                name_tag = name_zone.find("span")
                brandInfos["author_name"] = name_tag.get_text()

                cat_zone = sub_soup.find("div", class_="info-common-date")
                # print(cat_zone)
                if cat_zone:
                    cat_tag = cat_zone.find("a").get_text()
                    brandInfos["category"] = cat_tag
                else:
                    continue
                    brandInfos["category"] = ""

                time_zone = cat_zone.find("span", class_="fs-13 text-dark item-time").get_text()
                brandInfos["create_time"] = 0
                if time_zone[0].isdigit():
                    time_minus = re.findall(r"\d+", time_zone)
                    time_stamp = int(time.time()) - int(time_minus[0])*3600
                    brandInfos["create_time"] = time_stamp
                else:
                    # print(time_zone)
                    time_str = time_zone.split(' ')
                    if len(time_str) == 1:
                        time_stamp = int(time.time())
                        brandInfos["create_time"] = time_stamp
                    else:
                        time_month = time_str[0]
                        if time_month == "Jan":
                            time_month = 1
                        elif time_month == "Mar":
                            time_month = 2
                        elif time_month == "Apr":
                            time_month = 3
                        elif time_month == "May":
                            time_month = 4
                        elif time_month == "Jun":
                            time_month = 5
                        elif time_month == "Jun":
                            time_month = 6
                        elif time_month == "Jul":
                            time_month = 7
                        elif time_month == "Aug":
                            time_month = 8
                        elif time_month == "Sep":
                            time_month = 9
                        elif time_month == "Oct":
                            time_month = 10
                        elif time_month == "Nov":
                            time_month = 11
                        elif time_month == "Dec":
                            time_month = 12
                        else:
                            print ("month error!")
                        time_day = time_str[1]
                        time_str = "2018" + '-' + str(time_month) + '-' + time_day + " 00:00:00"
                        time_arr = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                        time_stamp = int(time.mktime(time_arr))
                        brandInfos["create_time"] = time_stamp
                # print(brandInfos["create_time"])

                brandInfos["tags"] = []
                tag_zone = sub_soup.find("div", class_="nowre-blogitem-tagwrap")
                for tag_tag in tag_zone.find_all("a"):
                    tag_text = tag_tag.get_text()
                    brandInfos["tags"].append(tag_text)


                brandInfos["author_figureurl"] = ""
                brandInfos["comment_num"] = 0
                brandInfos["like_num"] = 0
                brandInfos["comment_list"] = []

                brandInfos["content"] = []

                img_top_tone = sub_soup.find("div", class_="owl-carousel", id="horizontal-info-slide")
                if img_top_tone:
                    for img_top_tag in img_top_tone.find_all("img"):
                        content_all = {}
                        content_all["type"] = 2
                        content_all["text"] = img_top_tag["src"]
                        brandInfos["content"].append(content_all)

                video_zone = sub_soup.find("iframe", class_="nowre-player-iframe")
                if video_zone:
                    continue
                    # TODO: now video comment
                    content_all = {}
                    content_all["type"] = 1
                    content_all["text"] = video_zone["src"]
                    brandInfos["content"].append(content_all)

                content_zone = sub_soup.find("div", class_=re.compile("info-common-cont"))
                if content_zone:
                    for content_tag in content_zone.find_all("p"):
                        content_all = {}
                        img_tag = content_tag.find("img")
                        if img_tag:
                            content_all["type"] = 2
                            content_all["text"] = img_tag["src"]
                        else:
                            content_all["type"] = 3
                            content_all["text"] = content_tag.get_text()
                        brandInfos["content"].append(content_all)
                # print(brandInfos)
                file_name = "nowre{}.json".format(str(file_num))
                io.open(file_name, "a+", encoding="utf-8").write(
                json.dumps(brandInfos, sort_keys=True, ensure_ascii=False))
                # enter_line = '\r\n'
                # enter_line = enter_line.encode('utf-8')
                io.open(file_name, "a+").write("\n")

                io.open("nowre_dup.json", "w", encoding="utf-8").write(
                    json.dumps(nowre_dup, indent=4, sort_keys=True, ensure_ascii=False))


            # dgtle_dup[brand_name]["img"] = img_tag["src"]
            # youtube_url[brand_name]["img"] = img_tag["src"]
#             # FIXME: now time is all 2018
#             # time_zone = brand_soup.find("div", class_="author_name_box paBottom-10")
#             container_tag = brand_soup.find("div", id="container")
#             time_tag = container_tag.find("span", slot="date")
#             ####English version
#             # time_str = time_tag.get_text().lstrip("Published on ")
#             # time_month_str = time_str.split(' ')[0]
#             # time_month = 0
#             # if time_month_str == "Jan":
#             #     time_month = 1
#             # elif time_month_str == "Mar":
#             #     time_month = 2
#             # elif time_month_str == "Apr":
#             #     time_month = 3
#             # elif time_month_str == "May":
#             #     time_month = 4
#             # elif time_month_str == "Jun":
#             #     time_month = 5
#             # elif time_month_str == "Jun":
#             #     time_month = 6
#             # elif time_month_str == "Jul":
#             #     time_month = 7
#             # elif time_month_str == "Aug":
#             #     time_month = 8
#             # elif time_month_str == "Sep":
#             #     time_month = 9
#             # elif time_month_str == "Oct":
#             #     time_month = 10
#             # elif time_month_str == "Nov":
#             #     time_month = 11
#             # elif time_month_str == "Dec":
#             #     time_month = 12
#             # else:
#             #     print ("month error!")
#             # time_year_day = time_str.split(' ')[1]
#             # time_year = time_year_day.split(',')[1]
#             # time_day = time_year_day.split(',')[0]
#             # time_str = time_year + '-' + str(time_month) + '-' + time_day + " 00:00:00"
#
#             ###Chinese version
#             time_str = time_tag.get_text()
#             time_zone = re.findall(r"\d+", time_str)
#             time_year = time_zone[0]
#             time_month = time_zone[1]
#             time_day = time_zone[2]
#
#             time_str = time_year + '-' + time_month + '-' + time_day + " 00:00:00"
#             # print time_str
#             time_arr = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
#             time_stamp = int(time.mktime(time_arr))
#             brandInfos["create_time"] = time_stamp
#             # print time_stamp
#
#             # brandInfosAll.append(brandInfos)
#
#             if count % 300 == 0:
#                 file_num += 1
#             file_name = "youtube{}.json".format(str(file_num))
#             io.open(file_name, "a+", encoding="utf-8").write(
#                 json.dumps(brandInfos, sort_keys=True, ensure_ascii=False))
#             enter_line = '\n'
#             enter_line = enter_line.encode('utf-8')
#             open(file_name, "a+").write(enter_line)
#
#             if count % 5 == 0:
#                 io.open("youtube_dup.json", "w", encoding="utf-8").write(
#                     json.dumps(dgtle_dup, indent=4, sort_keys=True, ensure_ascii=False))

                # time.sleep(10)
            # time.sleep(3)
            # brandInfosAll = []

    except Exception as err:

        print("-" * 60)
        traceback.print_exc(file=sys.stdout)
        print("-" * 60)

    # print(count)


def usage():
    print(sys.argv[0] + ' -g xxxxs')


if __name__ == "__main__":
    nowre_main()