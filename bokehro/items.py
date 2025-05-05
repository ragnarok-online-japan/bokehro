# -*- coding: utf-8 -*-
#
# Copyright (c) MINETA "m10i" Hiroki <m10i0nyx.net>
# This software is released under the MIT License.
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class ItemSalesHistory(scrapy.Item):
    id = scrapy.Field()
    world = scrapy.Field()
    map_name = scrapy.Field()
    log_date = scrapy.Field()
    item_id = scrapy.Field()
    item_name = scrapy.Field()
    price = scrapy.Field()
    unit_price = scrapy.Field()
    count = scrapy.Field()
    slots = scrapy.Field()
    random_options = scrapy.Field()
    refining_level  = scrapy.Field()
    grade_level = scrapy.Field()
