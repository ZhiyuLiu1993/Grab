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


def chiphell_main():
    #原始网站：  https://www.chiphell.com/portal.php?mod=list&catid=66
    os.chdir("D:/网页抓取/chiphell_data")
    #TODO:  Deduplication(Done)

    count = 0
    file_num = 0
    url_count = 0

    #get titie tid url
    content_url = "https://www.chiphell.com/"
    base_title_url = "https://www.chiphell.com/portal.php?mod=list&catid="
    page_url = "&page="
    catid_num = [66, 126, 30, 47, 118, 46]

    chiphell_dup = {}
    chiphell_url = {}
    if os.path.exists("chiphell_dup.json"):
        chiphell_dup = json.loads(io.open("chiphell_dup.json", 'r', encoding='utf-8').read())

    try:
        for catid in catid_num:
            sub_url = base_title_url + str(catid) + page_url
            for i in range(1, 20):
                url = sub_url + str(i)
                # print(url)
                try:
                    f_raw_html = requests_get_text(url)
                except Exception as err:
                    print("err")
                    break
                # print(f_raw_html)
                html_soup = BeautifulSoup(f_raw_html, "lxml")
                # open("youtube.html", "w", encoding='utf-8').write(f_raw_html)
                for brand_tag in html_soup.find_all("dl", class_="bbda cl"):
                    url_count += 1
                    if url_count % 300 == 0:
                        file_num += 1
                    # print(brand_tag)
                    url_zone = brand_tag.find("a", target="_blank");
                    brand_name = url_zone["href"]
                    if brand_name in chiphell_dup:
                        continue
                    # print(brand_name)
                    chiphell_dup[brand_name] = {"id": brand_name}

                    brandInfos = {}
                    brandInfos["source_url"] = content_url + brand_name
                    print(brandInfos["source_url"])
                    brandInfos["title"] = url_zone.get_text()

                    cat_tag = brand_tag.find("label")
                    if cat_tag:
                        brandInfos["category"] = cat_tag.get_text()
                    elif catid == 46:
                        brandInfos["category"] = "新奇酷"
                    elif catid == 47:
                        brandInfos["category"] = "收藏爱好"
                    elif catid == 126:
                        brandInfos["category"] = "手表"


                    time_zone = brand_tag.find("span").get_text().strip()
                    time_str = time_zone + ":00"
                    time_arr = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    time_stamp = int(time.mktime(time_arr))
                    brandInfos["create_time"] = time_stamp

                    sub_html = requests_get_text(brandInfos["source_url"])
                    sub_soup = BeautifulSoup(sub_html, "lxml")

                    brandInfos["source_html"] = sub_html

                    comment_zone = sub_soup.find("div", class_="hm ptn")
                    comment_tag_num = 0
                    if comment_zone is None:
                        continue
                    for comment_tag in comment_zone.find_all("span", class_="xi1"):
                        # print(comment_tag)
                        if comment_tag_num == 1:
                            brandInfos["comment_num"] = comment_tag.get_text()
                        comment_tag_num += 1
                    com_num = min(int(brandInfos["comment_num"]), 10)
                    # print(com_num)

                    curnum = 0
                    brandInfos["content"] = []
                    brandInfos["comment_list"] = []
                    for content in sub_soup.find_all("div", id=re.compile("post_[1-9]\d*$")):
                        if curnum == 0:
                            author_fig_zone = content.find("div", class_="avatar")
                            brandInfos["author_figureurl"] = author_fig_zone.find("img")["src"]
                            author_name_zone = content.find("div", class_="authi")
                            brandInfos["author_name"] = author_name_zone.find("a").get_text()

                            content_detail_zone = content.find("td", class_="t_f", id=re.compile("postmessage"))
                            if content_detail_zone is None:
                                break
                            for content_detail in content_detail_zone.children:
                                # print(content_detail)
                                # print("---------------------------------------------------------------------------------")
                                # print("---------------------------------------------------------------------------------")
                                img_tag_zone = content_detail.find("img")
                                content_all = {}
                                if img_tag_zone == -1:
                                    content_all["type"] = 3
                                    content_all["text"] = content_detail
                                    if content_all["text"] == "":
                                        continue
                                elif img_tag_zone:
                                    # print(img_tag_zone)
                                    content_all["type"] = 2  # image
                                    try:
                                        content_all["text"] = img_tag_zone["file"]
                                    except Exception as err:
                                        continue
                                else:
                                    content_all["type"] = 3  # text
                                    # content_word = content_tag.find("p")
                                    # if content_word:
                                    content_all["text"] = content_detail.get_text()
                                    if content_all["text"] == "":
                                        continue
                                brandInfos["content"].append(content_all)

                            like_num_zone = content.find("td", class_="plc plm")
                            # print(like_num_zone)
                            # print(like_num_zone.find("span"))
                            like_num_tag = like_num_zone.find("span", id="favoritenumber")
                            if like_num_tag:
                                brandInfos["like_num"] = like_num_tag.get_text()
                            else:
                                brandInfos["like_num"] = 0
                                continue

                        else:
                            if com_num == 0:
                                break
                            com_num -= 1
                            comment_list_zone = content.find("td", class_="t_f", id=re.compile("postmessage"))
                            if comment_list_zone:
                                brandInfos["comment_list"].append(comment_list_zone.get_text())
                            else:
                                continue
                        curnum += 1
                    brandInfos["tags"] = []


                    # print(brandInfos)
                    file_name = "chiphell{}.json".format(str(file_num))
                    io.open(file_name, "a+", encoding="utf-8").write(
                    json.dumps(brandInfos, sort_keys=True, ensure_ascii=False))
                    # enter_line = '\r\n'
                    # enter_line = enter_line.encode('utf-8')
                    io.open(file_name, "a+").write("\n")

                    io.open("chiphell_dup.json", "w", encoding="utf-8").write(
                        json.dumps(chiphell_dup, indent=4, sort_keys=True, ensure_ascii=False))


    except Exception as err:

        print("-" * 60)
        traceback.print_exc(file=sys.stdout)
        print("-" * 60)

    # print(count)


def usage():
    print(sys.argv[0] + ' -g xxxxs')


if __name__ == "__main__":
    chiphell_main()