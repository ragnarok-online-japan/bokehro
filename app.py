#!/usr/bin/env python3

import os

import MySQLdb
import pandas as pd
from bokeh.embed import components
from bokeh.models import HoverTool
from bokeh.plotting import figure
from bokeh.resources import INLINE as resources_inline
from flask import Flask, render_template, request, jsonify
from jsonc_parser.parser import JsoncParser

app = Flask(__name__, template_folder='templates')
app.config['JSON_AS_ASCII'] = False

args: dict = {}
try:
    args: dict = JsoncParser.parse_file("config.jsonc")
except Exception as ex:
    print("[FATAL]", ex)
    raise ex

@app.route('/bokehro', methods=['GET'])
def bokehro():
    item_name = request.args.get("name")

    # init
    connection = None
    plot = None
    plot_script = ""
    plot_div = ""

    smelting_color_map={
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

    df = None

    if item_name is not None:
        try:
            connection = MySQLdb.connect(**args["mysql"])
            connection.autocommit(False)

            query_string = """
                SELECT datetime, unit_cost/1000000 AS 'unit_cost', smelting
                FROM item_detail_tbl
                WHERE item_name = %(item_name)s
                AND cards = '[]'
                AND enchants = '[]'
                ORDER BY 1 ASC, id ASC
                ;
            """

            df = pd.read_sql(query_string, connection, params={"item_name":item_name})

        except Exception as ex:
            raise ex
        finally:
            if connection is not None:
                connection.close()
        df['color']=[smelting_color_map[x] for x in df['smelting']]

        # figure作成
        plot = figure(title=item_name,
            x_axis_label = '日付',
            y_axis_label = 'MZeny',
            x_axis_type='datetime',
            tools=['pan','wheel_zoom','zoom_in','zoom_out','save','reset'],
            sizing_mode='stretch_both')

        # ベースにデータを配置
        plot.circle(source=df,
            x='datetime',
            y='unit_cost',
            color='color',
            fill_alpha=0.5)

        hover = HoverTool(
            tooltips=[("日時","@datetime{%F}"),("価格","@unit_cost M"),("精錬値","@smelting")],
            formatters={"@datetime":"datetime"}
        )
        plot.add_tools(hover)
        plot_script, plot_div = components(plot)

    # grab the static resources
    js_resources = resources_inline.render_js()
    css_resources = resources_inline.render_css()

    # render template
    html = render_template(
        "bokeh.html",
        item_name=item_name,
        plot_script=plot_script,
        plot_div=plot_div,
        js_resources=js_resources,
        css_resources=css_resources,
    )
    return html

@app.route('/bokehro-items', methods=['GET'])
def bokehro_items():
    items: list = []

    try:
        connection = MySQLdb.connect(**args["mysql"])
        connection.autocommit(False)

        query_string = """
            SELECT item_name
            FROM item_name_tbl
            ORDER BY 1 ASC
            ;
        """

        with connection.cursor() as cursor:
            cursor.execute(query_string)
            items = [item[0] for item in cursor.fetchall()]

    except Exception as ex:
        raise ex
    finally:
        if connection is not None:
            connection.close()

    return jsonify(items)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8081, debug=True)
