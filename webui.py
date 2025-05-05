#!/usr/bin/env python3.13

import re

from bokeh.embed import components
from bokeh.models import HoverTool
from bokeh.plotting import figure
from bokeh.resources import Resources as BokehResources

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from sqlalchemy.orm import Session
import uvicorn

from sql_app import crud
from sql_app.database import SessionLocal

app = FastAPI(
    title="bokehro",
    description="BokehRO - Bokeh for Ragnarok Online item sales history.",
    version="1.0.0")

templates = Jinja2Templates(directory="templates")

# Dependency
def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@app.get('/bokehro', tags=["bokehro"])
async def bokehro(
    request: Request,
    item_id: int = None,
    is_slots: str = None,
    is_random_options: str = None,
    is_round_cost: str = "G",
    refining: list[int] = [],
    db: Session = Depends(get_db_session)):

    # init
    plot = None
    plot_script: str = ""
    plot_div: str = ""

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

    df = []
    item_name: str = ""
    item_description: str = None

    if item_id is not None:
        result_sales_history = crud.get_item_sales_history(
            db=db,
            item_id=item_id,
            is_slots=is_slots,
            is_random_options=is_random_options,
            refining_levels=refining
        )

        result_data = crud.get_item_data_from_id(
            db=db,
            id=item_id
        )

        if result_data is not None:
            item_description = result_data.description
            if item_description is not None:
                item_description = item_description.replace("\n", "<br/>\n")

        df = pd.DataFrame(result_sales_history)

        if not df.empty:
            df['color']=[refining_color_map[x] for x in df['refining_level']]

            # figure作成
            plot = figure(
                title=result_data.displayname,
                x_axis_label='日付',
                y_axis_label='価格(Mz)',
                x_axis_type='datetime',
                tools=['box_zoom','reset','save'],
                sizing_mode='stretch_both')

            # ベースにデータを配置
            plot.circle(
                source=df,
                x='datetime',
                y='unit_cost',
                color='color',
                size=8,
                fill_alpha=0.5)

            hover = HoverTool(
                tooltips=[
                    ("ID", "@id"),
                    ("World", "@world"),
                    ("日時","@datetime{%F %R}"),
                    ("価格","@unit_cost"),
                    ("精錬値","@refining"),
                    ("カード/エンチャント","@slots"),
                    ],
                formatters={"@datetime":"datetime"}
            )
            plot.add_tools(hover)

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
            "item_count": len(df),
            "item_description": item_description,
            "is_slots": is_slots,
            "refining_list": refining,
            "plot_script": plot_script,
            "plot_div": plot_div,
            "resource_js": resource_js,
            "resource_css": resource_css
        },
    )
    return html

@app.get('/bokehro-item-suggest', tags=["bokehro"])
async def bokehro_item_suggest(
    db: Session = Depends(get_db_session)):

    result_item_suggest = crud.get_item_suggest(db=db)
    result = [dict(zip(["displayname"], row)) for row in result_item_suggest]

    # JSONで応答
    return JSONResponse(result)

if __name__ == "__main__":
    uvicorn.run(app=app, host="127.0.0.1")
