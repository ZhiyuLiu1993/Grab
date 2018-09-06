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
import math
from bs4 import BeautifulSoup
from builtins import str
from functools import reduce
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.request import Request
from urllib.parse import urlencode
from urllib.parse import urlsplit
import urllib
import getopt

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
                if not block:
                    break
                handle.write(block)
    except Exception as err:
        print(err)


# 失败重试
requests.adapters.DEFAULT_RETRIES = 5


def requests_get_text(url, retrys=3, params=params, headers=headers):
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


def dgtle_main():
    #原始网站： http://www.dgtle.com/dgtleforum.php
    os.chdir("D:/网页抓取/dgtle_data")

    #TODO:  Deduplication(Done)

    # get thread tid url
    base_url = "https://api.yii.dgtle.com/v2/forum-thread/thread?token=&dateline="
    time_stamp = int(time.time()) - 60
    print(time_stamp)
    # time_stamp = 1535358490
    sub_url = "&page=1&perpage=24&typeid=0"

    count = 0
    file_num = 0

    # get comment tid url
    base_comment_url = "https://api.yii.dgtle.com/v2/comment?token=&tid="
    sub_comment_url = "&page=1"

    #get titie tid url
    base_title_url = "http://www.dgtle.com/thread-"
    sub_title_url = "-1-1.html"

    dgtle_dup = {}
    if os.path.exists("dgtle_dup.json"):
        dgtle_dup = json.loads(io.open("dgtle_dup.json", 'r', encoding='utf-8').read())

    try:

        # f_raw_html = io.open("post.smzdm.com.html", 'r', encoding='utf-8')
        # for i in range(0, 3):
        #     r = requests.get(burl_base, params=params, headers=headers)
        # f_raw_html = urllib.urlopen(burl_base)
        start = 1
        stop = start + 15
        # start = 1
        # stop = 5
        for i in range(time_stamp, 1514736000, -60000):
            print(i)
            all_url = base_url + str(i) + sub_url
            # print all_url
            # url = "http://www.dgtle.com/dgtleforum.php"
            f_raw_html = requests_get_text(all_url)
            # f_raw_html = io.open("dgtle.html", 'r', encoding='utf-8')
            html_soup = BeautifulSoup(f_raw_html, "lxml")

            # for brand_tag in html_soup.find_all("h5", class_="z-feed-title"):
            for brand_tag in html_soup.find_all("tid"):
                brand_name = brand_tag.get_text()
                count += 1
                if count % 300 == 0:
                    file_num += 1
                if brand_name in dgtle_dup:
                    continue
                dgtle_dup[brand_name] = {"tid": brand_name}

                brandInfos = {}

                # brandInfos[brand_name] = {"source_url": brand_tag["href"]}

                brandInfos["source_url"] = base_title_url + brand_name + sub_title_url

                print(brandInfos["source_url"])

                brand_soup_html = requests_get_text(brandInfos["source_url"])

                # FIXME:  now comment
    #            brandInfos["source_url"] = brand_tag["href"]
                brandInfos["source_html"] = brand_soup_html
                brand_soup = BeautifulSoup(brand_soup_html, "lxml")
                title_zone = brand_soup.find("h2", class_="banner_title")
                # print title_zone
                if title_zone:
                    title_tag = title_zone.find("a")
                    brandInfos["title"] = title_zone.get_text()
                else:
                    # print "null name"
                    # continue
                    title_zone = brand_soup.find("div", class_="v-banner-info")
                    title_tag = title_zone.find("h3")
                    brandInfos["title"] = title_tag.get_text()

                    category_tag = title_zone.find("a")
                    # print category_tag
                    brandInfos["category"] = category_tag.get_text()

                    # FIXME: now time is all 2018
                    # time_zone = brand_soup.find("div", class_="author_name_box paBottom-10")
                    time_tag = title_zone.find("h5")
                    time_str = time_tag.get_text()
                    split_tag = title_zone.find("span").get_text()
                    time_str = time_str.split(split_tag)[1]
                    time_str = time_str.strip()
                    time_str = "2018-" + time_str + ":00"  #FIXME: if year before 2018 note this line
                    # print time_str
                    time_arr = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    time_stamp = int(time.mktime(time_arr))
                    brandInfos["create_time"] = time_stamp
                    # print time_stamp

                # print title_tag["content"]

                author_figure_zone = brand_soup.find("div", class_="banner_catdates")
                # print author_figure_zone
                if author_figure_zone:
                    author_figure_tag = author_figure_zone.find("img")
                    brandInfos["author_figureurl"] = author_figure_tag["src"]
                    # FIXME: now time is all 2018
                    # time_zone = brand_soup.find("div", class_="author_name_box paBottom-10")
                    time_tag = author_figure_zone.find("i")
                    time_str = time_tag.get_text()
                    time_str = "2018-" + time_str + ":00"
                    # print time_str
                    time_arr = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    time_stamp = int(time.mktime(time_arr))
                    brandInfos["create_time"] = time_stamp

                    author_tag = author_figure_zone.find("a", class_="view_author_name")
                    brandInfos["author_name"] = author_tag.get_text()

                    category_tag = author_figure_zone.find("a", class_="view_type")
                    brandInfos["category"] = category_tag.get_text()

                    comment_zone = brand_soup.find("div", id="comment_lists_box")
                    comment_num_zone = comment_zone.find("h4", class_="group-comment-title")
                    comment_tag = comment_num_zone.find("span")
                    brandInfos["comment_num"] = comment_tag.get_text()
                    # print brandInfos["comment_num"]

                    # comment_list_zone = comment_zone.find("ul", class_="comment-list cl")
                    # com_num = min(brandInfos["comment_num"], 10)
                    # # print com_num
                    # brandInfos["comment_list"] = []
                    #
                    # # TODO: now tag is null
                    # brandInfos["tags"] = []
                    #
                    # # tag_tag = brand_soup.find("body", itemtype="//schema.org/NewsArticle")
                    # # print tag_tag
                    #
                    # if comment_list_zone:
                    #     for com_first in comment_list_zone.find_all("li", class_="comment-item"):
                    #         if com_num <= 0:
                    #             break
                    #         comment_tag = com_first.find("p", class_="comment-summary")
                    #         brandInfos["comment_list"].append(comment_tag.get_text())
                    #         com_num -= 1
                    #         # print com_first.get_text()
                    #
                    content_zone = brand_soup.find("div", class_="view_content wp")
                    # print content_zone
                    brandInfos["content"] = []
                    for content_tag in content_zone.find_all("div", align="center"):
                        content_all = {}
                        if content_tag:
                            img_tag = content_tag.find("img")
                            if img_tag:
                                content_all["type"] = 2  # image
                                content_all["text"] = img_tag["src"]
                            else:
                                content_all["type"] = 3  # text
                                # content_word = content_tag.find("div", align="left")
                                # content_all["text"] = content_word.get_text()
                                content_all["text"] = content_tag.get_text()
                                if content_all["text"] == "":
                                    continue
                        else:
                            for content_tag in content_zone.next_elements:
                                print(content_tag)
                        brandInfos["content"].append(content_all)
                        # print content_all["text"]

                else:
                    #FIXME:!!!!!!

                    author_zone = brand_soup.find("div", class_="author-card-summary")
                    author_tag = author_zone.find("img")
                    brandInfos["author_figureurl"] = author_tag["src"]

                    name_zone = author_zone.find("a", class_="author-name")
                    brandInfos["author_name"] = name_zone.get_text().strip()
                    # print brandInfos["author_name"]

                    # like_zone = brand_soup.find("div", class_="banner_botfile")
                    # like_tag = like_zone.find("span")
                    # brandInfos["like_num"] = like_tag.get_text()
                    # print brandInfos["like_num"]

                    comment_num_zone = brand_soup.find("div", class_="banner_botfile")
                    comment_num_pre = comment_num_zone.find("a")
                    comment_num_tag = comment_num_pre.find_next_sibling("span")
                    brandInfos["comment_num"] = comment_num_tag.get_text()
                    # print brandInfos["comment_num"]

                    content_zone = brand_soup.find("div", class_="forum-viewthread-article-box")
                    # print content_zone
                    brandInfos["content"] = []
                    # tempnum = 0
                    for content_tag in content_zone.children:   #FIXME   now is wrong
                        # print tempnum
                        # tempnum += 1
                        # print content_tag
                        content_all = {}
                        pre_tag = content_tag.find("p")
                        if pre_tag:
                            if isinstance(pre_tag, int):    #important
                                content_all["type"] = 3  # text
                                # content_word = content_tag.find("p")
                                # if content_word:
                                # print content_tag
                                temp_content = str(content_tag)
                                # print  temp_content
                                # if temp_content.startswith(" "):
                                content_all["text"] = temp_content.strip()
                                if content_all["text"] == "":
                                    continue
                            else:
                                content_all["type"] = 3
                                content_all["text"] = content_tag.get_text()
                                if content_all["text"] == "":
                                    continue
                        else:
                            img_tag = content_tag.find("img")
                            if img_tag == -1:    #important
                                content_all["type"] = 3  # text
                                # content_word = content_tag.find("p")
                                # if content_word:
                                # print content_tag
                                temp_content = str(content_tag)
                                # print  temp_content
                                # if temp_content.startswith(" "):
                                content_all["text"] = temp_content.strip()
                                if content_all["text"] == "":
                                    continue
                            elif img_tag:
                                # print img_tag
                                content_all["type"] = 2  # image
                                content_all["text"] = img_tag["src"]
                            else:
                                content_all["type"] = 3  # text
                                # content_word = content_tag.find("p")
                                # if content_word:
                                content_all["text"] = content_tag.get_text()
                                if content_all["text"] == "":
                                    continue
                                #TODO  different type

                        brandInfos["content"].append(content_all)
                        # print brandInfos["content"]

                #dynamic comment list

                comment_list_zone = brand_soup.find("ul", class_="comment-list cl")
                # print comment_list_zone
                thread_num = comment_list_zone["data-tid"]
                # print thread_num
                com_num = min(int(brandInfos["comment_num"]), 10)
                # print com_num
                brandInfos["comment_list"] = []

                # TODO: now tag is null
                brandInfos["tags"] = []

                # tag_tag = brand_soup.find("body", itemtype="//schema.org/NewsArticle")
                # print tag_tag
                comment_url = base_comment_url + thread_num + sub_comment_url
                comment_html = requests_get_text(comment_url)
                comment_data = BeautifulSoup(comment_html, "lxml")

                if comment_data:
                    if com_num > 0:
                        for com_first in comment_data.find_all("comment"):
                            if com_num <= 0:
                                break
                            # print com_first.get_text()
                            brandInfos["comment_list"].append(com_first.get_text())
                            com_num -= 1

                like_zone = brand_soup.find("div", class_="like-num")
                like_tag = like_zone.find("span")
                brandInfos["like_num"] = like_tag.get_text()
                # print brandInfos["like_num"]



                # if like_tag
                #     brandInfos[brand_name]["like_num"] = like_tag.get_text()
                # brandInfosAll.append(brandInfos)

                file_name = "dgtle{}.json".format(str(file_num))
                io.open(file_name, "a+", encoding="utf-8").write(
                    json.dumps(brandInfos, sort_keys=True, ensure_ascii=False))
                io.open(file_name, "a+").write("\n")

                io.open("dgtle_dup.json", "w", encoding="utf-8").write(
                    json.dumps(dgtle_dup, indent=4, sort_keys=True, ensure_ascii=False))

                # time.sleep(10)

            # brandInfosAll = []

    except Exception as err:

        print("-" * 60)
        traceback.print_exc(file=sys.stdout)
        print("-" * 60)

    # 保存品牌信息
    #     io.open("smzdm.json", "w", encoding="utf-8").write(
    #         json.dumps(brandInfos, sort_keys=True, indent=4, ensure_ascii=False))
    print(count)


def usage():
    print(sys.argv[0] + ' -g xxxxs')


if __name__ == "__main__":
    dgtle_main()
