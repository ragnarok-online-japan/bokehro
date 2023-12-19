#!/bin/bash -l

cd /opt/bokeh-ro/tools

#------------------------------------------------------

cat << '_EOL_' | mysql pigeon -upigeon -p${MYSQL_PIGEON_PASSWORD}
DROP TABLE IF EXISTS item_suggest_tbl_tmp;
CREATE TABLE item_suggest_tbl_tmp (
    item_id bigint(1) UNSIGNED,
    item_name varchar(255)
);
INSERT INTO item_suggest_tbl_tmp(item_id, item_name)
SELECT DISTINCT item_id, item_name
FROM item_trade_tbl
WHERE item_id IS NOT NULL
ORDER BY 1;

SET SESSION lock_wait_timeout=1;
RENAME TABLE item_suggest_tbl TO item_suggest_tbl_delete, item_suggest_tbl_tmp TO item_suggest_tbl;
DROP TABLE item_suggest_tbl_delete;
_EOL_

#------------------------------------------------------

cat << '_EOL_' | mysql pigeon -upigeon -p${MYSQL_PIGEON_PASSWORD}
DROP TABLE IF EXISTS item_data_tbl_tmp;
CREATE TABLE item_data_tbl_tmp (
    item_id bigint(1) UNSIGNED DEFAULT NULL,
    item_name varchar(255),
    slot int(1) UNSIGNED DEFAULT NULL,
    description TEXT DEFAULT NULL,
    resname varchar(255) DEFAULT NULL,
    cardillustname varchar(255) DEFAULT NULL
);
_EOL_

./insert_itemdata.py --import-items /var/www/html_rodb/ROOD/items.json

cat << '_EOL_' | mysql pigeon -upigeon -p${MYSQL_PIGEON_PASSWORD}
ALTER TABLE item_data_tbl_tmp ADD PRIMARY KEY (item_id);
ALTER TABLE item_data_tbl_tmp ADD INDEX `idx_item_name_slot` (item_name, slot);
SET SESSION lock_wait_timeout=1;
RENAME TABLE item_data_tbl TO item_data_tbl_delete, item_data_tbl_tmp TO item_data_tbl;
DROP TABLE item_data_tbl_delete;
_EOL_
