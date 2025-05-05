from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from sql_app.models import ItemSalesHistoryTable, ItemDataTable, ItemSuggestTable

def get_item_sales_history(db: Session,
                           item_id: int,
                           is_slots: str|None = None,
                           is_random_options: str|None = None,
                           refining_levels: list[int] = [],
                           grade_levels: list[int] = []):
    query = db.query(ItemSalesHistoryTable)\
        .filter(ItemSalesHistoryTable.item_id == item_id)

    # filter by slots
    if is_slots is not None and is_slots != "":
        if is_slots == "_notempty_":
            query = query.filter(ItemSalesHistoryTable.slots != "[]")
        elif is_slots == "_empty_":
            query = query.filter(ItemSalesHistoryTable.slots == "[]")

    # filter by random options
    if is_random_options is not None and is_random_options != "":
        if is_random_options == "_notempty_":
            query = query.filter(ItemSalesHistoryTable.random_options != "[]")
        elif is_random_options == "_empty_":
            query = query.filter(ItemSalesHistoryTable.random_options == "[]")

    # filter by refining levels
    refining_level_list = [value for value in refining_levels if isinstance(value, int) == True]
    if len(refining_level_list) > 0:
        query = query.filter(ItemSalesHistoryTable.refining_level.in_(refining_level_list))

    # filter by grade levels
    grade_level_list = [value for value in grade_levels if isinstance(value, int) == True]
    if len(grade_level_list) > 0:
        query = query.filter(ItemSalesHistoryTable.grade_lebel.in_(grade_level_list))

    # order by datetime ascending
    query = query.order_by(asc(ItemSalesHistoryTable.log_date), asc(ItemSalesHistoryTable.id))

    return query.all()

def get_item_data_from_id(db: Session, id: int):
    query = db.query(ItemDataTable)\
        .filter(ItemDataTable.id == id)

    return query.first()

def get_item_data_from_displayname(db: Session, displayname: str, slot: int|None = None):
    query = db.query(ItemDataTable)\
        .filter(ItemDataTable.displayname == displayname)

    # filter by slot
    if slot is not None:
        query = query.filter(ItemDataTable.slot_num == slot)

    return query.first()

def get_item_data_list(db: Session, sort_by: str = "id", sort_order: str = "asc"):
    query = db.query(ItemDataTable)

    query = query.order_by(asc(getattr(ItemDataTable, sort_by)) if sort_order == "asc" else desc(getattr(ItemDataTable, sort_by)))

    return query.all()

def get_item_suggest(db: Session):
    return db.query(ItemSuggestTable, ItemSuggestTable.displayname).all()
