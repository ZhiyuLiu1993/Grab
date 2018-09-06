# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json
import os
import io
from scrapy.exceptions import DropItem
from scrapy.exporters import JsonLinesItemExporter


class MyspiderPipeline(object):
    def __init__(self):

        self.file = codecs.open('smzdm.json', 'a+', encoding='utf-8')

    def process_item(self, item, spider):
        # infos = {}
        # infos["source_url"] = item["source_url"]
        # infos["title"] = item["title"]
        # Need to convert item, otherwise each item is a list
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item

    # def spider_closed(self, spider):
    #     self.file.close()
    #
    #     file = codecs.open(filename, 'w+', encoding='utf-8')

# class


url_count = 0


class DuplicatesPipesline(object):
    def __init__(self):
        self.urls_seen = {}
        if os.path.exists("smzdm_dup.json"):
            self.urls_seen = json.loads(io.open("smzdm_dup.json", 'r', encoding='utf-8').read())

    def process_item(self, item, spider):
        global url_count
        url_count += 1
        if item["source_url"][0] in self.urls_seen:
            raise DropItem("Duplicate item found")
        else:
            self.urls_seen[item["source_url"][0]] = {}

            if url_count % 300 == 0:
                io.open("smzdm_dup.json", "w", encoding="utf-8").write(
                    json.dumps(self.urls_seen, indent=4, sort_keys=True, ensure_ascii=False))
            return item

    def __del__(self):
        if url_count:
            io.open("smzdm_dup.json", "w", encoding="utf-8").write(
                json.dumps(self.urls_seen, indent=4, sort_keys=True, ensure_ascii=False))


class TwoonespiderPipeline(object):
    def __init__(self):
        self.fp = open("duanzi.json", 'wb')
        self.exporter = JsonLinesItemExporter(self.fp, ensure_ascii=False, encoding='utf-8')
        self.fp.write(b"[")

    def open_spider(self, spider):
        pass

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        self.fp.write(b',')
        return item

    def close_spider(self, spider):
        self.fp.write(b"]")
        self.fp.close()
