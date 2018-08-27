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
from urlparse import urlparse
from urlparse import urlsplit
from urlparse import parse_qs
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


def wconcept_main():
    brand_cnt = 0

    os.chdir("wconcept_data")
    # 读取事先处理好的品牌json源文件
    graw_json = json.loads(io.open("girl_brandinfos.json", 'r', encoding='utf-8').read())
    braw_json = json.loads(io.open("boy_brandinfos.json", 'r', encoding='utf-8').read())
    brandInfos = {}
    if os.path.exists("wconcept.json"):
        brandInfos = json.loads(io.open("wconcept.json", 'r', encoding='utf-8').read())

    # 合并&过滤不需要字段
    burl_base = "https://www.wconcept.cn/brand/index/view/id/"
    for brand in graw_json["Brands"]:
        if brand["name"] in brandInfos:
            continue
        brandInfos[brand["name"]] = {"desc": brand["desc"], "brand_id": brand["brand_id"]
            , "product_count": brand["product_count"]
            , "logo": brand["logo_image_url"]
            , "sex": ['girl'], "items": []
            , "href": burl_base + brand["brand_id"]}
    for brand in braw_json["Brands"]:
        if brand["name"] in brandInfos:
            continue

        if brand["name"] in brandInfos:
            brandInfos[brand["name"]]["sex"].append('boy')
            continue
        brandInfos[brand["name"]] = {"desc": brand["desc"], "brand_id": brand["brand_id"]
            , "product_count": brand["product_count"]
            , "logo": brand["logo_image_url"]
            , "sex": ['girl'], "items": []
            , "href": burl_base + brand["brand_id"]}

    # 分析子页面，获取banner以及货品信息
    for brand in brandInfos:
        try:
            brand_cnt += 1
            # 检查信息是否已经补全
            if len(brandInfos[brand]["items"]) > 0:
                print(brand, "has grabed")
                continue


            # html_soup = BeautifulSoup(requests_get_text(brandInfos[brand]["href"]), 'lxml')
            # banner
            # banner_tag = html_soup.find("div", class_="top-banner owl-carousel-banner")
            # if banner_tag:
            # brandInfos[brand]["banner_img"] = banner_tag.img["src"]
            # 提取货品信息
            product_fmt = "https://www.wconcept.cn/brand/index/getSelectProduct/id/%s?limit=%s&status=1&sort=-updated_at&gender="
            j = json.loads(
                requests_get_text(product_fmt % (brandInfos[brand]["brand_id"], brandInfos[brand]["product_count"])))
            brandInfos[brand]["items"].append(j["items"])
            # 更新实际货品信息
            brandInfos[brand]["product_count"] = j["page"]["total_count"]
            # banner
            brandInfos[brand]["banner_img"] = j["banners"]

            print("=" * 30, brand, brand_cnt, brandInfos[brand]["product_count"])

            if brand_cnt % 30 == 0:
                io.open("wconcept.json", "w", encoding="utf-8").write(
                    json.dumps(brandInfos, sort_keys=True, indent=4, ensure_ascii=False))


        except Exception as err:
            print("-" * 60)
            traceback.print_exc(file=sys.stdout)
            print("-" * 60)

    # 保存品牌信息
    io.open("wconcept.json", "w", encoding="utf-8").write(
        json.dumps(brandInfos, sort_keys=True, indent=4, ensure_ascii=False))


def smzdm_main():
    brand_cnt = 0
    os.chdir("smzdm_data")
    # burl_base = "https://post.smzdm.com"

    brandInfosAll = []

    # if os.path.exists("smzdm.json"):
    #     brandInfos = json.loads(io.open("smzdm.json", 'r', encoding='utf-8').read())

    brandDouble = []
    file_count = 27
    count = 0

    for k in range(0, file_count):

        try:

            # f_raw_html = io.open("post.smzdm.com.html", 'r', encoding='utf-8')
            # for i in range(0, 3):
            #     r = requests.get(burl_base, params=params, headers=headers)
            # f_raw_html = urllib.urlopen(burl_base)
            start = k*15 + 1
            stop = start + 15
            # start = 1
            # stop = 5

            for i in range(start, stop):
                print i
                url = "https://post.smzdm.com/p{}/".format(str(i))
                # print f_raw_html.read()
                f_raw_html = requests_get_text(url)
                html_soup = BeautifulSoup(f_raw_html, "lxml")


                # print bandInfos
                # for brand_tag in html_soup.find_all("h5", class_="z-feed-title"):
                for brand_tag in html_soup.find_all("a", target="_blank", href=re.compile("https://post.smzdm.com/p/[1-9]\d*/$")):
                    brand_name = brand_tag["href"]

                    if brand_name.strip() in brandDouble:
                        continue
                    brandDouble.append(brand_name.strip())
                    count += 1

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

                    print brandInfos["source_url"]
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
                    com_num = min(comment_tag, 10)
                    # print com_num
                    brandInfos["comment_list"] = []

                    # TODO: now tag is null
                    brandInfos["tags"] = []

                    tag_tag = brand_soup.find("body", itemtype="//schema.org/NewsArticle")
                    # print tag_tag

                    if comment_list_zone:
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
                    file_name = "smzdm{}.json".format(str(k))
                    io.open(file_name, "a+", encoding="utf-8").write(
                        json.dumps(brandInfos, sort_keys=True, ensure_ascii=False))
                    enter_line = '\n'
                    enter_line = enter_line.encode('utf-8')
                    open(file_name, "a+").write(enter_line)


            # time.sleep(10)



            # brandInfosAll = []





        except Exception as err:


            print("-" * 60)
            traceback.print_exc(file=sys.stdout)
            print("-" * 60)

        # 保存品牌信息
        #     io.open("smzdm.json", "w", encoding="utf-8").write(
        #         json.dumps(brandInfos, sort_keys=True, indent=4, ensure_ascii=False))
    print count

def usage():
    print(sys.argv[0] + ' -g xxxxs')


if __name__ == "__main__":


    try:
        opts, args = getopt.getopt(sys.argv[1:], "g:", ["grap="])

        for opt, arg in opts:
            if opt in ('-g', '--grap'):
                if arg == 'wconcept':
                    wconcept_main()
                elif arg == 'smzdm':
                    smzdm_main()
            else:
                usage()

    except getopt.GetoptError:
        usage()

