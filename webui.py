#!/usr/bin/env python3.13

import re
from typing import Union

from bokeh.embed import components
from bokeh.models import HoverTool
from bokeh.plotting import figure
from bokeh.resources import Resources as BokehResources
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
import pandas as pd
import uvicorn

from sql_app.models import ItemSalesHistoryTable
from sql_app import crud, database

app = FastAPI(
    title="bokehro",
    description="BokehRO - Bokeh for Ragnarok Online item sales history.",
    version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "https://rodb.aws.0nyx.net",
        "https://rotool.gungho.jp"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

templates = Jinja2Templates(directory="templates")

refining_color_map={
    0:   "black",
    1:   "black",
    2:   "black",
    3:   "black",
    4:   "black",
    5:   "blue",
    6:   "blue",
    7:   "green",
    8:   "green",
    9:   "orange",
    10:  "red",
    None:"gray"
}

# SQLAlchemyのセッションを取得するための依存関係
# Dependency
def get_db_session():
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()

# SQLAlchemyオブジェクトを辞書形式に変換する関数
def to_dict(obj):
    return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}

# plot_item_sales_history
def plot_item_sales_history(
    item_id: int,
    is_slots: str,
    is_random_options: str,
    is_round_price: str,
    refining_levels: Union[list[int] | None],
    db: Session
):
    item_name: str = None
    item_description: str = None

    result_sales_history: list[ItemSalesHistoryTable] = crud.get_item_sales_history(
        db=db,
        item_id=item_id,
        is_slots=is_slots,
        is_random_options=is_random_options,
        refining_levels=refining_levels
    )

    result_data = crud.get_item_data_from_id(
        db=db,
        id=item_id
    )

    if result_data is not None:
        item_name = result_data.displayname
        item_description = result_data.description
        if item_description is not None:
            item_description = item_description.replace("\n", "<br/>\n")

    df = pd.DataFrame()  # 空のDataFrameを作成
    if len(result_sales_history) > 0:
        result_sales_history_dicts = [to_dict(row) for row in result_sales_history]
        del result_sales_history
        df = pd.DataFrame(result_sales_history_dicts)
        del result_sales_history_dicts

    y_axis_label = "価格(z)"
    if is_round_price == "K":
        y_axis_label = "価格(Kz)"
    elif is_round_price == "M":
        y_axis_label = "価格(Mz)"
    elif is_round_price == "G":
        y_axis_label = "価格(Gz)"
    elif is_round_price == "T":
        y_axis_label = "価格(Tz)"

    # figure作成
    plot = figure(
        title=item_name,
        x_axis_label='日付',
        y_axis_label=y_axis_label,
        x_axis_type='datetime',
        tools=['box_zoom','reset','save'],
        sizing_mode='stretch_width')

    if not df.empty:
        df['color']=[refining_color_map[x] for x in df['refining_level']]

        if is_round_price == "K":
            df['unit_price'] = df['unit_price'].apply(lambda x: round(x / 1000, 0))
        elif is_round_price == "M":
            df['unit_price'] = df['unit_price'].apply(lambda x: round(x / 1000000, 0))
        elif is_round_price == "G":
            df['unit_price'] = df['unit_price'].apply(lambda x: round(x / 1000000000, 0))
        elif is_round_price == "T":
            df['unit_price'] = df['unit_price'].apply(lambda x: round(x / 1000000000000, 0))

        # ベースにデータを配置
        plot.scatter(
            source=df,
            x='log_date',
            y='unit_price',
            color='color',
            size=8,
            fill_alpha=0.5)

        hover = HoverTool(
            tooltips=[
                    ("ID", "@id"),
                    ("World", "@world"),
                    ("Map", "@map_name"),
                    ("日時","@datetime{%F %R}"),
                    ("価格","@unit_price"),
                    ("精錬値","@refining"),
                    ("カード/エンチャント","@slots"),
                ],
            formatters={"@log_date":"datetime"}
        )
        plot.add_tools(hover)

    return plot, item_name, item_description, len(df)

@app.get('/bokehro', tags=["webui"])
@app.get('/bokehro/{item_id}', tags=["webui"])
async def bokehro(
    request: Request,
    item_id: int = None,
    item_name: str = None,
    is_slots: str = None,
    is_random_options: str = None,
    is_round_price: str = "M",
    refining_levels: Union[list[int]] = Query(default=None),
    db: Session = Depends(get_db_session)):

    # init
    plot = None
    plot_script: str = ""
    plot_div: str = ""
    item_count: int = 0
    item_description: str = None

    if item_id is None and item_name is not None:
        pattern = re.compile(r"^(.+)\[([0-9]+)\]$")
        match = pattern.match(item_name)
        slot = None
        if match is not None:
            item_name = match.group(1)
            slot = match.group(2)

        result_data = crud.get_item_data_from_displayname(
            db=db,
            displayname=item_name,
            slot=slot
        )

        if result_data is not None:
            item_id = result_data.id

    if item_id is not None:
        plot, item_name, item_description, item_count = plot_item_sales_history(
            item_id=item_id,
            is_slots=is_slots,
            is_random_options=is_random_options,
            is_round_price=is_round_price,
            refining_levels=refining_levels,
            db=db
        )

        plot_script, plot_div = components(plot)

    # grab the static resources
    resources = BokehResources(mode="cdn")
    resource_js = resources.render_js()
    resource_css = resources.render_css()

    # render template
    html = templates.TemplateResponse(
        name="bokehro.html",
        context={
            "request": request,
            "item_id": item_id,
            "item_name": item_name,
            "item_count": item_count,
            "item_description": item_description,
            "is_slots": is_slots,
            "is_random_options": is_random_options,
            "refining_levels": refining_levels,
            "plot_script": plot_script,
            "plot_div": plot_div,
            "resource_js": resource_js,
            "resource_css": resource_css
        },
    )
    return html

@app.get("/bokehro-check/{item_id}", tags=["api"])
async def bokehro_check(
    request: Request,
    item_id: int = None,
    db: Session = Depends(get_db_session)):

    item_name: str = ""
    item_highend = None

    result_data = crud.get_item_data_from_id(
        db=db,
        id=item_id
    )

    if result_data is None:
        response_body: dict = {
            "success" : False,
            "data" : {
                "item_id": item_id
            }
        }
        return JSONResponse(content=response_body, media_type="application/json", status_code=404)

    item_name = result_data.displayname
    response_body: dict = {
        "success" : True,
        "data" : {
            "item_id": item_id,
            "item_name": item_name,
            "highend": item_highend
        }
    }

    return JSONResponse(content=response_body, media_type="application/json")

@app.get("/bokehro-export-img/{item_id}", tags=["api"])
async def bokehro_export_img(
    request: Request,
    item_id: int = None,
    db: Session = Depends(get_db_session)):

    #if item_id is not None and item_id > 0:
    #    plot, _, _, _ = plot_item_sales_history(
    #        item_id=item_id,
    #        db=db
    #    )

    raise HTTPException(status_code=404, detail="sorry, not implemented yet")

@app.get('/bokehro-item-suggest', tags=["bokehro"])
async def bokehro_item_suggest(
    db: Session = Depends(get_db_session)):

    result_item_suggest = crud.get_item_suggest(db=db)
    result = [dict(zip(["displayname"], row)) for row in result_item_suggest]

    # JSONで応答
    return JSONResponse(result)

if __name__ == "__main__":
    uvicorn.run(app=app, host="127.0.0.1")
