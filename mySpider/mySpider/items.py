# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MyspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    source_url = scrapy.Field()
    source_html = scrapy.Field()
    title = scrapy.Field()
    tags = scrapy.Field()
    content = scrapy.Field()
    author_name = scrapy.Field()
    author_figureurl = scrapy.Field()
    comment_num = scrapy.Field()
    like_num = scrapy.Field()
    comment_list = scrapy.Field()
    catagory = scrapy.Field()
    create_time = scrapy.Field()
    pass
