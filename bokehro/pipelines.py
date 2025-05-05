# -*- coding: utf-8 -*-
#
# Copyright (c) MINETA "m10i" Hiroki <m10i0nyx.net>
# This software is released under the MIT License.
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json
from bokehro.sql_app import models
from bokehro.sql_app.database import Engine, SessionLocal
from sqlalchemy.dialects.mysql import insert

class MariaDbPipeline:
    def __init__(self, settings, *args, **kwargs):
        models.Base.metadata.create_all(bind=Engine)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            settings = crawler.settings,
        )

    def open_spider(self, spider):
        self.session = SessionLocal()

    def close_spider(self, spider):
        if self.session:
            try:
                self.session.close()
            except Exception as ex:
                spider.logger.error(f"Error closing session: {ex}")

    def process_item(self, item, spider):
        if spider.name in ['ItemSalesHistorySpider']:
            self.insert_item_sales_history(item, spider)
        elif spider.name in ['ItemSalesHistoryUpdate']:
            pass

        return item

    def insert_item_sales_history(self, item, spider):
        stmt = insert(models.ItemSalesHistoryTable).values(
            world=item['world'],
            map_name=item['map_name'],
            log_date=item['log_date'],
            item_name=item['item_name'],
            item_id=item['item_id'],
            price=item['price'],
            unit_price=item['unit_price'],
            count=item['count'],
            slots=json.dumps(item['slots'], ensure_ascii=False),
            random_options=json.dumps(item['random_options'], ensure_ascii=False),
            refining_level=item['refining_level'],
            grade_level=item['grade_level']
        )

        # ON DUPLICATE KEY UPDATEの設定
        stmt = stmt.on_duplicate_key_update(
            world=stmt.inserted.world,
            map_name=stmt.inserted.map_name,
            item_id=stmt.inserted.item_id,
            unit_price=stmt.inserted.unit_price,
            count=stmt.inserted.count,
            slots=stmt.inserted.slots,
            random_options=stmt.inserted.random_options,
            refining_level=stmt.inserted.refining_level,
            grade_level=stmt.inserted.grade_level
        )

        try:
            self.session.execute(stmt)
            self.session.commit()
        except Exception as ex:
            spider.logger.error(f"Error inserting item_sales_history: {ex}")
            try:
                self.session.rollback()
            except Exception as rollback_ex:
                pass
