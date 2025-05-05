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
            query = query.filter(ItemSalesHistoryTable.slots != '"[null, null, null, null]"')
        elif is_slots == "_empty_":
            query = query.filter(ItemSalesHistoryTable.slots == '"[null, null, null, null]"')

    # filter by random options
    if is_random_options is not None and is_random_options != "":
        if is_random_options == "_notempty_":
            query = query.filter(ItemSalesHistoryTable.random_options != '"[null, null, null, null, null]"')
        elif is_random_options == "_empty_":
            query = query.filter(ItemSalesHistoryTable.random_options == '"[null, null, null, null, null]"')

    # filter by refining levels
    if refining_levels is not None and len(refining_levels) > 0:
        query = query.filter(ItemSalesHistoryTable.refining_level.in_(refining_levels))

    # filter by grade levels
    if grade_levels is not None and len(grade_levels) > 0:
        query = query.filter(ItemSalesHistoryTable.grade_level.in_(grade_levels))

    # order by log_date ascending
    query = query.order_by(ItemSalesHistoryTable.log_date.asc())

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
