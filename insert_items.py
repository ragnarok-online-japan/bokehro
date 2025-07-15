#!/usr/bin/env python3.13

import argparse
import json
import re

from sql_app import models, crud, database
models.Base.metadata.create_all(bind=database.Engine)

parser = argparse.ArgumentParser(description='')

parser.add_argument('--import-items-json',
                    action='store',
                    nargs='?',
                    default='./items.json',
                    type=str,
                    help='import items.json')

args = parser.parse_args()

def main(args: argparse.Namespace) -> None:
    item_datas: dict = {}
    with open(args.import_items_json, 'r') as file:
        item_datas = json.load(file)

    with database.SessionLocal() as session:
        for item in item_datas.values():
            if "displayname" not in item or "id" not in item:
                continue

            item_data = models.ItemDataTable(
                id=item['id'],
                displayname=item['displayname'],
                description=item['description'],
                slot_num=item["slot"],
                type=item["type"]
            )
            # Check if the item already exists
            existing_item = crud.get_item_data_from_id(session, item['id'])
            if existing_item:
                session.delete(existing_item)
            session.add(item_data)
        session.commit()

if __name__ == '__main__':
    main(args)
