#!/usr/bin/env python3

import argparse
import csv
from datetime import datetime
import json
import re


from jsonc_parser.parser import JsoncParser
import pymysql

parser = argparse.ArgumentParser(description='')

args = parser.parse_args()

def main(args: dict):
    try:
        config: dict = JsoncParser.parse_file("../config.jsonc")
    except Exception as ex:
        print("[FATAL]", ex)
        raise ex

    try:
        connection = pymysql.connect(**config["mysql-ro"])

        query_select = """
            SELECT idt.id, idt.world, idt.`datetime`, idt.item_name, idt.cost, idt.unit_cost, idt.count, idt.cards, idt.enchants, idt.options, idt.refining, idt.update_time
            FROM item_detail_tbl AS idt
            ORDER BY 1 ASC;
        """

        with pymysql.cursors.SSDictCursor(connection) as cursor:
            cursor.execute(query_select)

            with open("import.csv", "w", encoding="utf-8") as fp:
                csv_writer = csv.writer(fp)

                while True:
                    item = cursor.fetchone()
                    if item is None:
                        break

                    item_id: int = item["id"]
                    world: str = item["world"]
                    log_date = item["datetime"]
                    item_name: str = item["item_name"]
                    price: int = item["cost"]
                    unit_price: int = item["unit_cost"]
                    item_count: int = item["count"]
                    cards_org: list = json.loads(item["cards"])
                    enchants_org: list = json.loads(item["enchants"])
                    options_org: list = json.loads(item["options"])
                    refining_level: int = item["refining"]
                    update_time: datetime = item["update_time"]

                    # initialize
                    cards: list = [None, None, None, None]
                    random_options: list = [None, None, None, None, None]
                    idx_cards: int = 0
                    idx_random_options: int = 0
                    card_slot_num: int = 0

                    matches = re.match(r"^.*\[(\d+)\]$", item_name)
                    if matches is not None:
                        card_slot_num = int(matches.group(1))

                    if "[ECO] ミニー" in enchants_org:
                        enchants_org.remove("[ECO] ミニー")
                        enchants_org.remove("ドゥ")
                        cards_org.remove("アルマカード")
                        cards_org.append("[ECO] ミニー・ドゥ・アルマカード")

                    if "[ECO] サラマンダー" in enchants_org:
                        enchants_org.remove("[ECO] サラマンダー")
                        cards_org.remove("アルマカード")
                        cards_org.append("[ECO] サラマンダー・アルマカード")

                    if "[ECO] タイニー" in enchants_org:
                        enchants_org.remove("[ECO] タイニー")
                        cards_org.remove("アルマカード")
                        cards_org.append("[ECO] タイニー・アルマカード")

                    if "[ECO] モーモー" in enchants_org:
                        enchants_org.remove("[ECO] モーモー")
                        cards_org.remove("アルマカード")
                        cards_org.append("[ECO] モーモー・アルマカード")

                    if "[ECO] ブリキングRX1" in enchants_org:
                        enchants_org.remove("[ECO] ブリキングRX1")
                        cards_org.remove("アルマカード")
                        cards_org.append("[ECO] ブリキングRX1・アルマカード")

                    if "ペル&キスミー" in enchants_org:
                        enchants_org.remove("ペル&キスミー")
                        cards_org.remove("ペルカード")
                        cards_org.append("ペル&キスミー・ペルカード")

                    if "シンギング" in enchants_org:
                        enchants_org.remove("シンギング")
                        enchants_org.remove("ペル&スイング")
                        cards_org.remove("ペルカード")
                        cards_org.append("シンギング・ペル&スイング・ペルカード")

                    if "フェルス" in enchants_org:
                        enchants_org.remove("フェルス")
                        cards_org.remove("リヒテルンカード")
                        cards_org.append("フェルス・リヒテルンカード")

                    if "アハトカード" in cards_org:
                        enchants_org.remove("魔神の使徒")
                        cards_org.remove("アハトカード")
                        cards_org.append("魔神の使徒・アハトカード")

                    if "シナイムカード" in cards_org:
                        enchants_org.remove("魔神の使徒")
                        cards_org.remove("シナイムカード")
                        cards_org.append("魔神の使徒・シナイムカード")

                    count_cards: int = len(cards_org)
                    count_enchats: int = len(enchants_org)
                    count_options: int = len(options_org)

                    try:
                        flag = False
                        if (count_cards + count_enchats) <= 4:
                            for idx, value in enumerate(cards_org):
                                cards[idx] = value
                                idx_cards = idx + 1

                            for idx, value in enumerate(enchants_org):
                                cards[idx + idx_cards] = value

                            flag = True

                        if (count_enchats + count_options) == 5:
                            for idx, value in enumerate(enchants_org):
                                random_options[idx] = value
                                idx_random_options = idx + 1

                            for idx, value in enumerate(options_org):
                                random_options[idx + idx_random_options] = value

                            flag = True

                        if count_options == 5:
                            for idx, value in enumerate(options_org):
                                random_options[idx] = value

                            flag = True

                        if (count_cards + count_enchats + count_options) > 0 and flag == False:
                            print("[WARNING]", item_id, item)
                            continue
                    except IndexError:
                        print("[ERROR]", item_id, item)
                        continue

                    if refining_level is None:
                        refining_level = 0

                    csv_writer.writerow([
                        item_id,
                        item_name,
                        str(log_date),
                        world,
                        "NULL",
                        price,
                        unit_price,
                        item_count,
                        json.dumps(cards, ensure_ascii=False),
                        json.dumps(random_options, ensure_ascii=False),
                        refining_level,
                        str(update_time)
                        ])

    except Exception as ex:
        raise ex
    finally:
        if connection is not None:
            connection.close()

if __name__ == '__main__':
    main(args)
