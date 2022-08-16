#!/usr/bin/env python3

import re
import MySQLdb
import pandas as pd
from bokeh.embed import components
from bokeh.models import HoverTool
from bokeh.plotting import figure
from bokeh.resources import INLINE as resources_inline
from flask import Flask, jsonify, render_template, request
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
    item_name: str           = request.args.get("name", default="")
    is_card: str             = request.args.get("is_card", default="_all_")
    is_enchant: str          = request.args.get("is_enchant", default="_all_")
    is_round_cost: bool      = request.args.get("is_round_cost", default=True, type=bool)
    smelting_list: list[int] = request.args.getlist("smelting[]", type=int)

    # init
    connection = None
    plot = None
    plot_script: str = ""
    plot_div: str = ""

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
    item_id:int = None
    item_description: str = None

    if item_name is not None:
        try:
            connection = MySQLdb.connect(**args["mysql"])
            connection.autocommit(False)

            sql_unit_cost = "unit_cost/1000000"
            if is_round_cost == False:
                sql_unit_cost = "unit_cost"

            query_item_detail: str = """
                SELECT id, datetime, {:s} AS 'unit_cost', smelting, cards, enchants
                FROM item_detail_tbl
                WHERE item_name = %(item_name)s
            """.format(sql_unit_cost)

            if is_card == "_all_":
                pass
            elif is_card == "_none_":
                query_item_detail += " AND cards = '[]'"
            elif is_card == "_required_":
                query_item_detail += " AND cards != '[]'"

            if is_enchant == "_all_":
                pass
            elif is_enchant == "_none_":
                query_item_detail += " AND enchants = '[]'"
            elif is_enchant == "_required_":
                query_item_detail += " AND enchants != '[]'"

            smelting_list = [value for value in smelting_list if isinstance(value, int) == True]
            if len(smelting_list) > 0:
                query_item_detail += " AND smelting IN({:s})".format(",".join(map(str, smelting_list)))

            query_item_detail += " ORDER BY 1 ASC, id ASC;"

            df = pd.read_sql(query_item_detail, connection, params={"item_name":item_name})

            query_item_data: str = """
                SELECT item_id, description
                FROM item_data_tbl
                WHERE item_name = %(item_name)s
                AND slot = %(slot)s;
            """
            item_search_name: str = item_name
            slot: int = 0
            match = re.match(r"^(.+)\[([0-9])\]$", item_name)
            if match:
                item_search_name = match.group(1)
                slot = int(match.group(2))

            with connection.cursor() as cursor:
                cursor.execute(query_item_data, {"item_name":item_search_name, "slot":slot})
                item_row = cursor.fetchone()
                if item_row is not None:
                    item_id = item_row[0]
                    item_description = item_row[1]
                    if item_description is not None:
                        item_description = item_description.replace("\n", "<br/>\n")

        except Exception as ex:
            raise ex
        finally:
            if connection is not None:
                connection.close()

        df['color']=[smelting_color_map[x] for x in df['smelting']]

        # figure作成
        plot = figure(
            title=item_name,
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
                ("日時","@datetime{%F %R}"),
                ("価格","@unit_cost"),
                ("精錬値","@smelting"),
                ("カード","@cards"),
                ("エンチャント","@enchants")
                ],
            formatters={"@datetime":"datetime"}
        )
        plot.add_tools(hover)

        plot_script, plot_div = components(plot)

    # grab the static resources
    js_resources = resources_inline.render_js()
    css_resources = resources_inline.render_css()

    # render template
    html = render_template(
        "bokehro.html",
        item_name=item_name,
        item_count=len(df),
        item_id=item_id,
        item_description=item_description,
        is_card=is_card,
        is_enchant=is_enchant,
        smelting_list=smelting_list,
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
            FROM item_suggest_tbl
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
