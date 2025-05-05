from sqlalchemy import CheckConstraint, Column, DateTime, String, Text
from sqlalchemy.dialects.mysql import BIGINT as BigInteger
from sqlalchemy.dialects.mysql import INTEGER as Integer
from sqlalchemy.dialects.mysql import TIMESTAMP as Timestamp
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.schema import Index, UniqueConstraint
from sqlalchemy.sql.expression import text

from sql_app.database import Base


class ItemDataTable(Base):
    __tablename__ = "item_data_tbl"
    __table_args__=(
        Index("idx_displayname", "displayname"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_row_format": "DYNAMIC"}
    )
    id = Column(Integer(1, unsigned=True), primary_key=True)
    displayname = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    slot_num = Column(Integer(1, unsigned=True), nullable=True)
    type = Column(String(256), nullable=True)

class ItemSalesHistoryTable(Base):
    __tablename__ = "item_sales_history_tbl"
    __table_args__=(
        Index("idx_item_id", "item_id"),
        Index("idx_item_name", "item_name"),
        Index("idx_log_date", "log_date"),
        UniqueConstraint("world", "map_name", "log_date", "item_id", "unit_price", "count", "slots", "random_options", "refining_level", "grade_level", name="uq_item_sales_history"),
        CheckConstraint("JSON_VALID(slots)", name="ck_slots"),
        CheckConstraint("JSON_VALID(random_options)", name="ck_random_options"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_row_format": "DYNAMIC"}
    )

    id = Column(BigInteger(1, unsigned=True), primary_key=True, autoincrement=True)
    world = Column(String(32), nullable=False)
    map_name = Column(String(256), nullable=True)
    log_date = Column(DateTime, nullable=False)
    item_id = Column(Integer(1, unsigned=True), nullable=False)
    item_name = Column(String(256), nullable=False)
    price = Column(BigInteger(1, unsigned=True), nullable=False)
    unit_price = Column(BigInteger(1, unsigned=True), nullable=False)
    count = Column(Integer(1, unsigned=True), nullable=False)
    slots = Column(JSON, nullable=False, default="[]")
    random_options = Column(JSON, nullable=False, default="[]")
    refining_level = Column(Integer(1, unsigned=True), nullable=True, default=None)
    grade_level = Column(Integer(1, unsigned=True), nullable=True, default=None)
    updated_at = Column(Timestamp, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True)

class ItemSuggestTable(Base):
    __tablename__ = "item_suggest_tbl"
    __table_args__=(
        Index("idx_displayname", "displayname"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_row_format": "DYNAMIC"}
    )

    id = Column(Integer(1, unsigned=True), primary_key=True, autoincrement=True)
    displayname = Column(String(256), unique=True, nullable=False)
