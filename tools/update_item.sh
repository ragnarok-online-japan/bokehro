#!/bin/bash -l

wget -q -O items.json https://ragnarokonline.0nyx.net/assets/json/items.json \
 && ./get_item_img.py --export-path /var/www/html/item_img/

cat << '_EOL_' | mysql pigeon -upigeon -p${MYSQL_PIGEON_PASSWORD}
DROP TABLE item_suggest_tbl_tmp;
CREATE TABLE item_suggest_tbl_tmp (item_name varchar(255), item_id bigint(1) UNSIGNED DEFAULT NULL, description TEXT DEFAULT NULL);
INSERT INTO item_suggest_tbl_tmp(item_name) SELECT DISTINCT item_name FROM item_detail_tbl ORDER BY 1;
_EOL_

./attachment_item_id.py

cat << '_EOL_' | mysql pigeon -upigeon -p${MYSQL_PIGEON_PASSWORD}
ALTER TABLE item_suggest_tbl_tmp ADD PRIMARY KEY (item_name);
ALTER TABLE item_suggest_tbl_tmp ADD INDEX `idx_item_id` (item_id);
BEGIN;
RENAME TABLE item_suggest_tbl TO item_suggest_tbl_delete, item_suggest_tbl_tmp TO item_suggest_tbl;
DROP TABLE item_suggest_tbl_delete;
COMMIT;
_EOL_


cat << '_EOL_' | mysql pigeon -upigeon -p${MYSQL_PIGEON_PASSWORD}
DROP TABLE item_data_tbl_tmp;
CREATE TABLE item_data_tbl_tmp (item_id bigint(1) UNSIGNED DEFAULT NULL, item_name varchar(255), slot int(1) UNSIGNED DEFAULT NULL, description TEXT DEFAULT NULL);
_EOL_

./insert_item_data.py

cat << '_EOL_' | mysql pigeon -upigeon -p${MYSQL_PIGEON_PASSWORD}
ALTER TABLE item_data_tbl_tmp ADD PRIMARY KEY (item_id);
ALTER TABLE item_data_tbl_tmp ADD INDEX `idx_item_name_slot` (item_name, slot);
BEGIN;
RENAME TABLE item_data_tbl TO item_data_tbl_delete, item_data_tbl_tmp TO item_data_tbl;
DROP TABLE item_data_tbl_delete;
COMMIT;
_EOL_


cat << '_EOL_' | mysql pigeon -upigeon -p${MYSQL_PIGEON_PASSWORD}
DROP TABLE item_enchant_tbl_tmp;
CREATE TABLE item_enchant_tbl_tmp (enchant varchar(255));
ALTER TABLE item_enchant_tbl_tmp ADD PRIMARY KEY (enchant);
_EOL_

./insert_enchant_names.py

cat << '_EOL_' | mysql pigeon -upigeon -p${MYSQL_PIGEON_PASSWORD}
BEGIN;
RENAME TABLE item_enchant_tbl TO item_enchant_tbl_delete, item_enchant_tbl_tmp TO item_enchant_tbl;
DROP TABLE item_enchant_tbl_delete;
COMMIT;
_EOL_
