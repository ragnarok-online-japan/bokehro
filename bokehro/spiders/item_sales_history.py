# -*- coding: utf-8 -*-
#
# Copyright (c) MINETA "m10i" Hiroki <m10i0nyx.net>
# This software is released under the MIT License.
#

from datetime import datetime
import re
import scrapy
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.spiders import CrawlSpider
from twisted.internet.error import DNSLookupError, TimeoutError
import time

from bokehro.items import ItemSalesHistory
from sql_app import crud
from sql_app.database import SessionLocal


class ItemSalesHistorySpider(CrawlSpider):
    name = 'ItemSalesHistorySpider'

    allowed_domains = [
        'rotool.gungho.jp'
    ]

    item_id: int = None

    def __init__(self, settings, item_id: int = None, *args, **kwargs):
        super(ItemSalesHistorySpider, self).__init__(*args, **kwargs)
        self.item_id = item_id

    @classmethod
    def from_crawler(cls, crawler, item_id: int = None):
        return cls(settings = crawler.settings, item_id = item_id)

    def start_requests(self):
        if self.item_id is None:
            item_list = []
            with SessionLocal() as session:
                item_list = crud.get_item_data_list(
                    db=session,
                    sort_by="id",
                    sort_order="desc")

            for row in item_list:
                yield scrapy.Request(
                    f"https://rotool.gungho.jp/item_trade_log_filtered_search/?item_id={row.id}",
                    meta = {
                        "dont_redirect": True
                    },
                    errback=self.errback_httpjson,
                    callback=self.parse_httpjson,
                    cb_kwargs={
                        "item_id": int(row.id)
                    }
                )

        else:
            yield scrapy.Request(
                f"https://rotool.gungho.jp/item_trade_log_filtered_search/?item_id={self.item_id:s}",
                meta = {
                    "dont_redirect": True
                },
                errback=self.errback_httpjson,
                callback=self.parse_httpjson,
                cb_kwargs={
                    "item_id": int(self.item_id)
                }
            )

    def parse_httpjson(self, response, item_id: int = None):
        matches = re.search(r"/item_trade_log_filtered_search/.*$", response.url)
        if matches is None:
            return

        if response.status != 200:
            self.logger.warning(f'Got failed response status code {response.status} from {response.url}')
            return

        data_json = response.json()
        if data_json == "none":
            return

        for original in data_json:
            item_sales_history = ItemSalesHistory()
            item_sales_history["item_id"] = item_id
            item_sales_history["item_name"] = original["item_name"]
            item_sales_history["log_date"] = datetime.strptime(original['log_date'], "%Y-%m-%d %H:%M:%S.%f")
            item_sales_history["world"] = original["world"]
            item_sales_history["map_name"] = original["mapname"]
            item_sales_history["price"] = int(original["price"])
            item_sales_history["unit_price"] = int(int(original["price"]) / int(original["item_count"]))
            item_sales_history["count"] = int(original["item_count"])
            item_sales_history["slots"] = [
                original["card1"],
                original["card2"],
                original["card3"],
                original["card4"]
            ]
            item_sales_history["random_options"] = [
                original["RandOption1"],
                original["RandOption2"],
                original["RandOption3"],
                original["RandOption4"],
                original["RandOption5"]
            ]
            item_sales_history["refining_level"] = int(original["refining_level"])
            item_sales_history["grade_level"] = int(original["GradeLevel"])

            yield item_sales_history

    def errback_httpjson(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            # you can get the response
            response = failure.value.response
            self.logger.warning('HttpError on {} (status:{})'.format(response.url, response.status))

            # 403エラーの場合にスリープ
            if response.status == 403:
                self.logger.warning("403 Forbidden detected. Sleeping for 60 seconds...")
                time.sleep(60)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.warning('DNSLookupError on {}'.format(request.url))

        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.warning('TimeoutError on {}'.format(request.url))
