#!/bin/bash -l

wget -q -O items.json https://ragnarokonline.0nyx.net/assets/json/items.json \
 && ./get_item_img.py --export-path /var/www/html/item_img/ >/dev/null

cat << '_EOL_' | mysql pigeon -upigeon -p${MYSQL_PIGEON_PASSWORD}
DROP TABLE item_name_tbl_tmp;
CREATE TABLE item_name_tbl_tmp (item_name varchar(255), item_id bigint(1) UNSIGNED DEFAULT NULL, description TEXT DEFAULT NULL);
INSERT INTO item_name_tbl_tmp(item_name) SELECT DISTINCT item_name FROM item_detail_tbl ORDER BY 1;
ALTER TABLE item_name_tbl_tmp ADD PRIMARY KEY (item_name);
_EOL_

./attachment_item_id.py

cat << '_EOL_' | mysql pigeon -upigeon -p${MYSQL_PIGEON_PASSWORD}
BEGIN;
RENAME TABLE item_name_tbl TO item_name_tbl_delete, item_name_tbl_tmp TO item_name_tbl;
DROP TABLE item_name_tbl_delete;
COMMIT;
_EOL_
