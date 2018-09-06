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

params = {};
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



def smzdm_main():
    #原始网站： https://post.smzdm.com
    brand_cnt = 0
    os.chdir("D:/网页抓取/smzdm_data")
    # burl_base = "https://post.smzdm.com"

    brandInfosAll = []
    file_num = 0

    # if os.path.exists("smzdm.json"):
    #     brandInfos = json.loads(io.open("smzdm.json", 'r', encoding='utf-8').read())

    smzdm_dup = {}
    count = 0
    if os.path.exists("smzdm_dup.json"):
        smzdm_dup = json.loads(io.open("smzdm_dup.json", 'r', encoding='utf-8').read())

    try:

        # f_raw_html = io.open("post.smzdm.com.html", 'r', encoding='utf-8')
        # for i in range(0, 3):
        #     r = requests.get(burl_base, params=params, headers=headers)
        # f_raw_html = urllib.urlopen(burl_base)
        # start = 1
        # stop = 5

        for i in range(1, 100):
            # print(i)
            url = "https://post.smzdm.com/p{}/".format(str(i))
            # print f_raw_html.read()
            f_raw_html = requests_get_text(url)
            html_soup = BeautifulSoup(f_raw_html, "lxml")


            # print bandInfos
            # for brand_tag in html_soup.find_all("h5", class_="z-feed-title"):
            for brand_tag in html_soup.find_all("a", target="_blank", href=re.compile("https://post.smzdm.com/p/[1-9]\d*/$")):
                brand_name = brand_tag["href"]

                count += 1
                if count % 100 == 0:
                    file_num += 1
                if brand_name in smzdm_dup:
                    continue
                smzdm_dup[brand_name] = {"id": brand_name}
                io.open("smzdm_dup.json", "w", encoding="utf-8").write(
                    json.dumps(smzdm_dup, indent=4, sort_keys=True, ensure_ascii=False))

                brandInfos = {}

                # print source_url
                #if brand_name in brandInfos:
                    # print(source_url, " has graped")
                    # print("graped")
                 #   continue

                #brandInfos[brand_name] = {"source_url": brand_tag["href"]}
                brand_soup_html = requests_get_text(brand_tag["href"])
                # print brand_tag["href"]

                #FIXME:  now comment
                brandInfos["source_url"] = brand_tag["href"]
                brandInfos["source_html"] = brand_soup_html
                brand_soup = BeautifulSoup(brand_soup_html, "lxml")
                title_tag = brand_soup.find("h1", itemprop="headline", class_="item-name")
                brandInfos["title"] = title_tag.get_text()
                    # print title_tag["content"]
                time_tag = brand_soup.find("span", class_="xilie", attrs={"itemprop": "author"})
                null_name = time_tag.find("span", class_="grey", itemprop="name")
                time_str = ""
                if null_name:
                    time_str = null_name.find_next_sibling("span", class_="grey").get_text().strip()
                    brandInfos["author_name"] = null_name.get_text()
                    # author_figure_zone = brand_soup.find("div", "user_tx")
                    # author_figure_tag = author_figure_zone.find("img")
                    brandInfos["author_figureurl"] = ""
                else:
                    time_str = time_tag.find("span", class_="grey").get_text().strip()
                    author_tag = brand_soup.find("a", attrs={"itemprop": "name"})
                    brandInfos["author_name"] = author_tag.get_text()
                    author_figure_zone = brand_soup.find("div", "user_tx")
                    author_figure_tag = author_figure_zone.find("img")
                    brandInfos["author_figureurl"] = author_figure_tag["src"]
                # time_str.decode('string_escape')
                # time_str.replace("\r\n", " ")
                # time_str.strip()
                # print time_str

                print(brandInfos["source_url"])
                time_arr = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                time_stamp = int(time.mktime(time_arr))
                brandInfos["create_time"] = time_stamp


                # print brandInfos[brand_name]["create_time"]
                    # print time_stamp


                # print brandInfos[brand_name]["author_name"]

                category_tag = author_tag.find_next_sibling("a")
                if category_tag:
                    brandInfos["category"] = category_tag.get_text()

                like_tag = brand_soup.find("span", class_="Number").get_text().strip()
                brandInfos["like_num"] = like_tag
                # like_num = like_tag.get_text()
                # like_num.strip()

                comment_tag = brand_soup.find("em", class_="commentNum").get_text()
                brandInfos["comment_num"] = comment_tag
                # print brandInfos[brand_name]["comment_num"]


                # print brandInfos[brand_name]["author_figure"]

                comment_list_zone = brand_soup.find("div", class_="comment_wrap", id="comment")
                com_num = min(int(comment_tag), 10)
                # print com_num
                brandInfos["comment_list"] = []

                # TODO: now tag is null
                brandInfos["tags"] = []

                tag_tag = brand_soup.find("body", itemtype="//schema.org/NewsArticle")
                # print tag_tag

                if comment_list_zone:
                    if com_num > 0:
                        for com_first in comment_list_zone.find_all("span", itemprop="description"):
                            if com_num <= 0:
                                break
                            brandInfos["comment_list"].append(com_first.get_text())
                            com_num -= 1
                            # print com_first.get_text()

                content_zone = brand_soup.find("article")
                # print content_zone
                brandInfos["content"] = []
                for content_tag in content_zone.find_all("p", itemprop="description"):
                    content_all = {}
                    img_tag = content_tag.find("img")
                    if img_tag:
                        content_all["type"] = 2   #image
                        content_all["text"] = img_tag["src"]
                    else:
                        content_all["type"] = 3   #text
                        content_all["text"] = content_tag.get_text()
                        if content_all["text"] == "":
                            continue
                    brandInfos["content"].append(content_all)
                    # print content_all["text"]


                # if like_tag
                #     brandInfos[brand_name]["like_num"] = like_tag.get_text()
                #brandInfosAll.append(brandInfos)
                file_name = "smzdm{}.json".format(str(file_num))
                # file_name = "smzdmtemp.json"
                io.open(file_name, "a+", encoding="utf-8").write(
                    json.dumps(brandInfos, sort_keys=True, ensure_ascii=False))
                io.open(file_name, "a+").write("\n")

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
    smzdm_main()


