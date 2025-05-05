#!/usr/bin/env python3.13

import argparse
import re

import pandas as pd

from sql_app import models, crud, database
models.Base.metadata.create_all(bind=database.Engine)

parser = argparse.ArgumentParser(description='')

parser.add_argument('--import-items-jsonl',
                    action='store',
                    nargs='?',
                    default='./items.jsonl',
                    type=str,
                    help='import items.jsonl')

args = parser.parse_args()

def main(args):
    df = pd.read_json(args.import_items_jsonl, orient='records', lines=True)

    if df.empty:
        print('No items to insert')
        return

    pattern = re.compile(r".*\[([0-9]+)\]$")

    with database.SessionLocal() as session:
        for row in df.iterrows():
            slot: int|None = None
            matches = pattern.match(row[1]['displayname'])
            if matches:
                slot = int(matches.group(1))

            item_data = models.ItemDataTable(
                id=row[1]['id'],
                displayname=row[1]['displayname'],
                description=row[1]['description'],
                slot_num=slot
            )
            # Check if the item already exists
            existing_item = crud.get_item_data_from_id(session, row[1]['id'])
            if existing_item:
                session.delete(existing_item)
            session.add(item_data)
        session.commit()

if __name__ == '__main__':
    main(args)
