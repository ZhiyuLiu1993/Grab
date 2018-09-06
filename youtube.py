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

from selenium import webdriver
from selenium.webdriver.common.action_chains import  ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

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
            print ("ok")
            return r.text
        except requests.exceptions.ConnectionError:
            print(url, str(i), "Connection refused")
            time.sleep(5)
        except Exception as err:
            print(url, str(i), err)
            time.sleep(5)

    return ''


def youtube_main():
    #原始网站：  https://www.youtube.com/channel/UCurLNabeCMo9vaGpcswDg5Q
    os.chdir("D:/网页抓取/youtube_data")

    #TODO:  Deduplication(Done)

    count = 0
    file_num = 0

    #get titie tid url
    base_title_url = "https://www.youtube.com"

    dgtle_dup = {}
    youtube_url = {}
    if os.path.exists("youtube_dup.json"):
        dgtle_dup = json.loads(io.open("youtube_dup.json", 'r', encoding='utf-8').read())

    # options = Options()
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--proxy-server=https://10.14.87.100:8080')
    # driver = webdriver.Chrome(chrome_options=options)

    try:

        # f_raw_html = io.open("post.smzdm.com.html", 'r', encoding='utf-8')
        # for i in range(0, 3):
        #     r = requests.get(burl_base, params=params, headers=headers)
        # f_raw_html = urllib.urlopen(burl_base)

        url = "https://www.youtube.com/channel/UCurLNabeCMo9vaGpcswDg5Q/videos"
        driver = webdriver.Chrome()
        driver.maximize_window()

        # f_raw_html = download(url, proxy='10.14.87.100:8080')   #

        # f_raw_html = requests_get_text(url)

        url_count = 0
        driver.implicitly_wait(3)
        driver.get(url)
        scroll_time = 17
        for i in range(1, scroll_time):
            js = "var q=document.documentElement.scrollTop=100000"
            driver.execute_script(js)
            time.sleep(1)
        f_raw_html = driver.page_source
        # driver.quit()
        # print(f_raw_html)

        # print(f_raw_html)
        # f_raw_html = io.open("dgtle.html", 'r', encoding='utf-8')
        html_soup = BeautifulSoup(f_raw_html, "lxml")
        # print(html_soup)
        for brand_tag in html_soup.find_all("div", id="dismissable"):
            brandInfos = {}
            # print(brand_tag)
            brand_zone = brand_tag.find("a", id="video-title")
            brand_name = brand_zone["href"]
            url_count += 1
            if url_count % 300 == 0:
                file_num += 1
            if brand_name in dgtle_dup:
                continue
            time_filter_zone = brand_tag.find("span", class_="style-scope ytd-thumbnail-overlay-time-status-renderer")
            time_filter = time_filter_zone.get_text().strip()
            time_min = time_filter.split(":")[0]
            if int(time_min) > 9:
                continue
            img_tag = brand_tag.find("img", id="img")
            try:
                dgtle_dup[brand_name] = {"img": img_tag["src"]}
                youtube_url[brand_name] = {"img": img_tag["src"]}
            except Exception as err:
                continue
            brandInfos["source_url"] = base_title_url + brand_name
            brandInfos["source_html"] = ""

            brandInfos["title"] = brand_zone["title"]
            name_tag = brand_tag.find("a", spellcheck="false")
            brandInfos["author_name"] = name_tag.get_text()
            brandInfos["tags"] = []
            brandInfos["author_figureurl"] = ""
            brandInfos["comment_num"] = 0
            brandInfos["like_num"] = 0
            brandInfos["category"] = "Sneaker Collecting"
            brandInfos["create_time"] = 0
            brandInfos["comment_list"] = []
            brandInfos["content"] = []
            content_all = {}
            content_all["type"] = 1
            content_all_string = brand_name.split("=")[1]
            content_all_string = "MP4/" + content_all_string + ".mp4"
            content_all["file_name"] = content_all_string
            content_all["text"] = ""
            brandInfos["content"].append(content_all)
            content_all = {}
            content_all["type"] = 2
            # content_all["text"] = youtube_url[brand_name]["img"]
            content_all["file_name"] = "img/" + brand_name.split("=")[1] + ".jpg"
            brandInfos["content"].append(content_all)
            # img_filename = content_all_string +".webp"
            # urllib.request.urlretrieve(content_all["text"], img_filename)

            # download_img(img_filename, content_all_string)

            # print(brandInfos)
            print(brand_name)
            file_name = "youtube{}.json".format(str(file_num))
            io.open(file_name, "a+", encoding="utf-8").write(
                json.dumps(brandInfos, sort_keys=True, ensure_ascii=False))
            # enter_line = '\r\n'
            # enter_line = enter_line.encode('utf-8')
            io.open(file_name, "a+").write("\n")

            io.open("youtube_dup.json", "w", encoding="utf-8").write(
                json.dumps(dgtle_dup, indent=4, sort_keys=True, ensure_ascii=False))


            # dgtle_dup[brand_name]["img"] = img_tag["src"]
            # youtube_url[brand_name]["img"] = img_tag["src"]
        # open("youtube.html", "w").write(f_raw_html)
        print(url_count)
        driver.quit()

        # time.sleep(15)
        # driver2 = webdriver.Chrome()
        # driver2.implicitly_wait(30)
        # driver2.maximize_window()

            # for brand_tag in html_soup.find_all("h5", class_="z-feed-title"):
#         for brand_tag in youtube_url:
#             brand_name = brand_tag
#             # print(brand_name)
#
#             # if brand_name in dgtle_dup:
#             #     continue
#             # dgtle_dup[brand_name] = {"tid": brand_name}
#             count += 1
#
#             brandInfos = {}
#
#             # brandInfos[brand_name] = {"source_url": brand_tag["href"]}
#
#             brandInfos["source_url"] = base_title_url + brand_name
#
#             # print brandInfos["source_url"]
#
#             # brand_soup_html = requests_get_text(brandInfos["source_url"])
#             # brand_soup_html = download(brandInfos["source_url"])
#
#             driver2.get(brandInfos["source_url"])
#             # locator = (By.ID, "container")
#             # WebDriverWait(driver2, 4, 0.5).until(
#             #     EC.presence_of_element_located(locator)
#             # )
#             for i in range(1, 2):
#                 js = "var q=document.documentElement.scrollTop=10000"
#                 driver2.execute_script(js)
#                 time.sleep(1)
#             time.sleep(30)
#             # click = driver2.find_element_by_link_text('展开')
#             # ActionChains(driver2).move_to_element(click).perform()
#             brand_soup_html = driver2.page_source
#             # print(brand_soup_html)
#
#             # FIXME:  now comment
# #            brandInfos["source_url"] = brand_tag["href"]
#             brandInfos["source_html"] = brand_soup_html
#             brand_soup = BeautifulSoup(brand_soup_html, "lxml")
#             title_zone = brand_soup.find("yt-formatted-string", class_="style-scope ytd-video-primary-info-renderer")
#             # print title_zone
#             if title_zone:
#                 brandInfos["title"] = title_zone.get_text()
#                 # print "null name"
#
#             # category_tag = title_zone.find("")
#             # print category_tag
#             # brandInfos["category"] = category_tag.get_text()
#             # FIXME:Now is fixed
#             brandInfos["category"] = "Sneaker Collecting"
#
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
#             # print title_tag["content"]
#
#             author_figure_zone = brand_soup.find("yt-img-shadow", id="avatar")
#             author_figure_tag = author_figure_zone.find("img")
#             brandInfos["author_figureurl"] = author_figure_tag["src"]
#
#             author_name_zone = brand_soup.find("div", id="upload-info")
#             author_name_tag = author_name_zone.find("a")
#             brandInfos["author_name"] = author_name_tag.get_text()
#
#             # TODO: now tag is null
#             brandInfos["tags"] = []
#
#             brandInfos["content"] = []
#             content_all = {}
#             content_all["type"] = 1
#             content_all_string = brand_name.split("=")[1]
#             content_all["text"] = content_all_string
#             brandInfos.append(content_all)
#             content_all = {}
#             content_all["type"] = 2
#             content_all["text"] = youtube_url[brand_name]["img"]
#             brandInfos.append(content_all)
#             content_all = {}
#             content_all["type"] = 3
#             content_all_three = brand_soup.find("yt-formatted-string", class_="content style-scope ytd-video-secondary-info-renderer")
#             content_all["text"] = content_all_three.get_text()
#             brandInfos.append(content_all)
#
#             like_zone = brand_soup.find("yt-formatted-string", id="text")
#             # like_string = like_zone["aria-label"]
#             # like_num_tag = re.findall(r"\d+", like_string)
#             # like_num = ''.join(like_num_tag)
#             # brandInfos["like_num"] = like_num
#             brandInfos["like_num"] = like_zone.get_text()
#
#
#             # comment_list_zone = brand_soup.find("ul", class_="comment-list cl")
#             # # print comment_list_zone
#             # thread_num = comment_list_zone["data-tid"]
#             # # print thread_num
#             # com_num = min(brandInfos["comment_num"], 10)
#             # # print com_num
#             # brandInfos["comment_list"] = []
#             #
#             # # TODO: now tag is null
#             # brandInfos["tags"] = []
#
#             # tag_tag = brand_soup.find("body", itemtype="//schema.org/NewsArticle")
#             # print tag_tag
#             # comment_url = base_comment_url + thread_num + sub_comment_url
#             # comment_html = requests_get_text(comment_url)
#             # comment_data = BeautifulSoup(comment_html, "lxml")
#
#             # if comment_data:
#             #     for com_first in comment_data.find_all("comment"):
#             #         if com_num <= 0:
#             #             break
#             #         # print com_first.get_text()
#             #         brandInfos["comment_list"].append(com_first.get_text())
#             #         com_num -= 1
#
#             # print brandInfos["like_num"]
#
#
#
#             # if like_tag
#             #     brandInfos[brand_name]["like_num"] = like_tag.get_text()
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

    # 保存品牌信息
    #     io.open("smzdm.json", "w", encoding="utf-8").write(
    #         json.dumps(brandInfos, sort_keys=True, indent=4, ensure_ascii=False))
    # print(count)


def usage():
    print(sys.argv[0] + ' -g xxxxs')


if __name__ == "__main__":
    youtube_main()
