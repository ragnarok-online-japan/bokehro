#!/usr/bin/env python3

# pip3 install pyquery aiohttp Pillow

import argparse
import json
import re

import MySQLdb
from jsonc_parser.parser import JsoncParser

parser = argparse.ArgumentParser(description='')

args = parser.parse_args()

def main(args: dict):
    try:
        config: dict = JsoncParser.parse_file("../config.jsonc")
    except Exception as ex:
        print("[FATAL]", ex)
        raise ex

    try:
        connection = MySQLdb.connect(**config["mysql"])
        connection.autocommit(False)

        query_select = """
            SELECT DISTINCT enchants
            FROM item_detail_tbl
            WHERE enchants != '[]';
        """

        query_insert = """
            INSERT INTO item_enchant_tbl_tmp(enchant)
            VALUES(%s)
            ;
        """

        enchant_list: list = []
        with connection.cursor() as cursor:
            cursor.execute(query_select)
            enchants = cursor.fetchall()
            for enchant in enchants:
                enchant_list.extend(json.loads(enchant[0]))

        enchant_list = list(set(enchant_list))
        enchant_list.sort()

        with connection.cursor() as cursor:
            cursor.executemany(query_insert, enchant_list)

        connection.commit()

    except Exception as ex:
        raise ex
    finally:
        if connection is not None:
            connection.close()

if __name__ == '__main__':
    main(args)
