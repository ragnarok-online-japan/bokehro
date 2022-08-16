#!/usr/bin/env python3

import argparse
import json

import MySQLdb
from jsonc_parser.parser import JsoncParser

parser = argparse.ArgumentParser(description='')

parser.add_argument('--import-items',
                    action='store',
                    nargs='?',
                    default='./items.json',
                    type=str,
                    help='import items.json')

args = parser.parse_args()

def main(args: dict):
    try:
        config: dict = JsoncParser.parse_file("../config.jsonc")
    except Exception as ex:
        print("[FATAL]", ex)
        raise ex

    item_list = {}
    with open(args.import_items, "r", encoding="utf-8") as fp:
        item_list = json.load(fp)

    if len(item_list) == 0:
        print("[FATAL]", "item_list is None")
        exit(0)

    try:
        connection = MySQLdb.connect(**config["mysql"])
        connection.autocommit(False)

        query_insert = """
            INSERT INTO item_data_tbl_tmp(item_name, item_id, slot, description)
            VALUES(%s, %s, %s, %s)
            ;
        """

        item_ids: list = []
        for key, values in item_list.items():
            item_id: int = int(key)
            item_name: str = values["displayname"]
            description: str = values["description"]
            slot: int = 0
            if "slot" in values:
                slot = values["slot"]
            item_ids.append((item_name, item_id, slot, description))

        with connection.cursor() as cursor:
            cursor.executemany(query_insert, item_ids)

        connection.commit()

    except Exception as ex:
        raise ex
    finally:
        if connection is not None:
            connection.close()

if __name__ == '__main__':
    main(args)
