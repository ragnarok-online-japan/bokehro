#!/usr/bin/env python3

import MySQLdb
from jsonc_parser.parser import JsoncParser

def main():
    try:
        config: dict = JsoncParser.parse_file("../config.jsonc")
    except Exception as ex:
        print("[FATAL]", ex)
        raise ex

    try:
        connection = MySQLdb.connect(**config["mysql"])
        connection.autocommit(False)

        select_query = """
            SELECT item_id, item_name, slot
            FROM item_data_tbl
            ORDER BY 1 ASC
            ;
        """

        update_query = """
            UPDATE item_trade_tbl
            SET item_id = %s
            WHERE item_name = %s
            ;
        """

        with connection.cursor() as cursor:
            cursor.execute(select_query)
            rows = cursor.fetchall()

            for row in rows:
                item_id = row[0]
                item_name = row[1]
                slot = (row[2])
                print(item_id)

                if slot == 0:
                    cursor.execute(update_query, [item_id, f"{item_name:s}"])

                cursor.execute(update_query, [item_id, f"{item_name:s}[{slot:d}]"])

        connection.commit()

    except Exception as ex:
        raise ex
    finally:
        if connection is not None:
            connection.close()

if __name__ == '__main__':
    main()
