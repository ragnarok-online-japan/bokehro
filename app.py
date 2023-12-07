#!/usr/bin/env python3

import itertools
import json
import os
import re
from io import StringIO
import tempfile
from urllib.parse import quote_plus

import pandas as pd
import pymysql
from bokeh.embed import components
from bokeh.models import HoverTool
from bokeh.plotting import figure
from bokeh.resources import CDN, INLINE as resources_inline
from bokeh.io import export_png
from flask import (Flask, Response, jsonify, make_response, render_template, request, send_file)
from flask_cors import CORS
from jsonc_parser.parser import JsoncParser
from selenium import webdriver
#import redis

app = Flask(__name__, template_folder="templates")
app.config["JSON_AS_ASCII"] = False
CORS(app,
     resources={
         r"^/bokehro.*": {
             "origins": [
                 "http://localhost",
                 "https://rodb.aws.0nyx.net",
                 "https://rotool.gungho.jp"
             ]
         }
     }
)

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

args: dict = {}
try:
    args: dict = JsoncParser.parse_file("config.jsonc")
except Exception as ex:
    print("[FATAL]", ex)
    raise ex

@app.route("/bokehro", methods=["GET", "POST"])
def bokehro():
    item_name: str            = request.args.get("name", default="", type=str)
    refinings: list[int]      = request.args.getlist("refining[]", type=int)

    card_enchants: list[str]  = request.args.getlist("card_enchants[]", type=str)
    random_options: list[str] = request.args.getlist("random_options[]", type=str)

    # init
    connection = None
    plot = None
    plot_script: str = ""
    plot_div: str = ""

    df = None
    item_count: int = 0
    item_id:int = None
    item_description: str = None
    item_resname: str = None
    card_enchant_list: list = []
    random_option_list: list = []

    item_history_keys: list[str] = []
    #try:
    #    redis_conn = redis.Redis(host="localhost", port=6379, db=0, encoding="utf-8")
    #    item_history_keys = redis_conn.keys("*")
    #except:
    #    pass

    if item_name is not None and item_name != "":
        try:
            connection = pymysql.connect(**args["mysql-ro"])

            query_item_trade: str = """
                SET STATEMENT max_statement_time=10
                FOR SELECT id, log_date, unit_price/1000000 AS 'unit_price', world, map_name, refining_level, cards, random_options
                FROM item_trade_tbl
                WHERE item_name = %(item_name)s
            """

            refinings = [value for value in refinings if isinstance(value, int) == True]
            if len(refinings) > 0:
                query_item_trade += " AND refining_level IN({:s})".format(",".join(map(str, refinings)))

            if len(card_enchants) > 0:
                for value in card_enchants:
                    query_item_trade += " AND JSON_CONTAINS(cards, '\"{:s}\"', '$')".format(
                        connection.escape_string(value.replace("%","%%")))

            if len(random_options) > 0:
                for value in random_options:
                    query_item_trade += " AND JSON_CONTAINS(random_options, '\"{:s}\"', '$')".format(
                        connection.escape_string(value.replace("%","%%")))

            query_item_trade += " ORDER BY 1 ASC;"

            df = pd.read_sql(sql=query_item_trade, con=connection, params={"item_name":item_name})

            #if len(df) > 0:
            #    try:
            #        count = redis_conn.get(item_name.encode("utf-8"))
            #        if count is None:
            #            count = 1
            #        else:
            #            count = int(count) + 1
            #        redis_conn.set(item_name, count, keepttl=(60*60*24))
            #    except:
            #        pass

            for value in df["cards"].to_list():
                json_list = json.loads(value)
                json_list = set(json_list)
                if None in json_list:
                    json_list.remove(None)
                card_enchant_list.append(json_list)
            card_enchant_list = sorted(set(itertools.chain.from_iterable(card_enchant_list)))

            for value in df["random_options"].to_list():
                json_list = json.loads(value)
                json_list = set(json_list)
                if None in json_list:
                    json_list.remove(None)
                random_option_list.append(json_list)
            random_option_list = sorted(set(itertools.chain.from_iterable(random_option_list)))

            query_item_data: str = """
                SET STATEMENT max_statement_time=1
                FOR SELECT item_id, description, cardillustname
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

                    item_resname = f"{item_id:d}"
                    if item_row[2] is not None:
                        item_resname = f"{item_id:d}_cardillust"

                    if item_description is not None:
                        item_description = item_description.replace("\n", "<br/>\n")

        except Exception as ex:
            raise ex
        finally:
            if connection is not None:
                connection.close()

        item_count = len(df)

        df['color']=[refining_color_map[x] for x in df['refining_level']]

        # figure作成
        plot = figure(
            title=item_name,
            x_axis_label='日付',
            y_axis_label='価格(Mz)',
            x_axis_type='datetime',
            tools=['box_zoom','reset','save'],
            sizing_mode='stretch_width')

        # ベースにデータを配置
        plot.circle(
            source=df,
            x='log_date',
            y='unit_price',
            color='color',
            size=12,
            fill_alpha=0.5)

        hover = HoverTool(
            tooltips=[
                ("ID", "@id"),
                ("World", "@world"),
                ("Map", "@map_name"),
                ("日時","@log_date{%F %R}"),
                ("価格","@unit_price"),
                ("精錬値","@refining_level"),
                ("カード/エンチャント","@cards"),
                ("ランダムオプション","@random_options")
                ],
            formatters={"@log_date":"datetime"}
        )
        plot.add_tools(hover)

        plot_script, plot_div = components(plot)

    # grab the static resources
    js_resources = resources_inline.render_js()
    css_resources = resources_inline.render_css()

    #for idx, item_name_bin in enumerate(item_history_keys):
    #    item_history_keys[idx] = item_name_bin.decode("utf-8")

    # render template
    html = render_template(
        "bokehro.html",
        item_name=item_name,
        item_count=item_count,
        item_id=item_id,
        item_description=item_description,
        item_resname=item_resname,
        refinings=refinings,
        card_enchant_list=card_enchant_list,
        random_option_list=random_option_list,
        card_enchants=card_enchants,
        random_options=random_options,
        plot_script=plot_script,
        plot_div=plot_div,
        js_resources=js_resources,
        css_resources=css_resources,
        item_history_keys=item_history_keys
    )
    return html

@app.route("/bokehro-export-img")
def bokehro_export_img():
    item_name: str            = request.args.get("name", default="", type=str)
    refinings: list[int]      = request.args.getlist("refining[]", type=int)

    card_enchants: list[str]  = request.args.getlist("card_enchants[]", type=str)
    random_options: list[str] = request.args.getlist("random_options[]", type=str)

    # init
    connection = None

    if item_name is not None and item_name != "":
        try:
            connection = pymysql.connect(**args["mysql-ro"])
            query_item_trade: str = """
                SET STATEMENT max_statement_time=10
                FOR SELECT id, log_date, unit_price/1000000 AS 'unit_price', world, map_name, refining_level, cards, random_options
                FROM item_trade_tbl
                WHERE item_name = %(item_name)s
            """

            refinings = [value for value in refinings if isinstance(value, int) == True]
            if len(refinings) > 0:
                query_item_trade += " AND refining_level IN({:s})".format(",".join(map(str, refinings)))

            if len(card_enchants) > 0:
                for value in card_enchants:
                    query_item_trade += " AND JSON_CONTAINS(cards, '\"{:s}\"', '$')".format(
                        connection.escape_string(value.replace("%","%%")))

            if len(random_options) > 0:
                for value in random_options:
                    query_item_trade += " AND JSON_CONTAINS(random_options, '\"{:s}\"', '$')".format(
                        connection.escape_string(value.replace("%","%%")))

            query_item_trade += " ORDER BY 1 ASC;"

            df = pd.read_sql(sql=query_item_trade, con=connection, params={"item_name":item_name})

        except Exception as ex:
            raise ex
        finally:
            if connection is not None:
                connection.close()

        df['color']=[refining_color_map[x] for x in df['refining_level']]

        # figure作成
        plot = figure(
            title=item_name,
            x_axis_label='日付',
            y_axis_label='価格(Mz)',
            x_axis_type='datetime',
            tools=[]
        )

        # ベースにデータを配置
        plot.circle(
            source=df,
            x='log_date',
            y='unit_price',
            color='color',
            size=12,
            fill_alpha=0.5)

        with tempfile.NamedTemporaryFile(delete=True, suffix=".png") as temp:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            driver = webdriver.Chrome(options)
            export_png(plot, filename=temp.name, webdriver=driver, width=1280, height=720)

            return send_file(temp.name, mimetype="image/png", as_attachment=True, download_name=f"bokehro_{item_name}.png")

    # other
    return Response(status=404)

@app.route("/bokehro-check", methods=["GET", "POST"])
def bokehro_check():
    item_name: str            = request.args.get("name", default="", type=str)
    refinings: list[int]      = request.args.getlist("refining[]", type=int)

    card_enchants: list[str]  = request.args.getlist("card_enchants[]", type=str)
    random_options: list[str] = request.args.getlist("random_options[]", type=str)

    # init
    connection = None

    item_id: int = None

    if item_name is not None and item_name != "":
        try:
            connection = pymysql.connect(**args["mysql-ro"])

            query_item_trade: str = """
                SET STATEMENT max_statement_time=10
                FOR SELECT id
                FROM item_trade_tbl
                WHERE item_name = %(item_name)s
            """

            refinings = [value for value in refinings if isinstance(value, int) == True]
            if len(refinings) > 0:
                query_item_trade += " AND refining_level IN({:s})".format(",".join(map(str, refinings)))

            if len(card_enchants) > 0:
                for value in card_enchants:
                    query_item_trade += " AND JSON_CONTAINS(cards, '\"{:s}\"', '$')".format(
                        connection.escape_string(value.replace("%","%%")))

            if len(random_options) > 0:
                for value in random_options:
                    query_item_trade += " AND JSON_CONTAINS(random_options, '\"{:s}\"', '$')".format(
                        connection.escape_string(value.replace("%","%%")))

            query_item_trade += " ORDER BY 1 ASC;"

            df = pd.read_sql(sql=query_item_trade, con=connection, params={"item_name":item_name})

            query_item_data: str = """
                SET STATEMENT max_statement_time=1
                FOR SELECT item_id, cardillustname
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

        except Exception as ex:
            raise ex
        finally:
            if connection is not None:
                connection.close()

    response = None
    response_body: dict = {
        "success" : True,
        "request" : {
            "item_name" : item_name,
            "refinings" : refinings
        },
        "item_id": item_id
    }

    if df is not None and len(df) > 0:
        response_body["export_img_url"] = f"https://{request.host}/bokehro-export-img?name=" + quote_plus(item_name)
    else:
        response_body["export_img_url"] = f"https://{request.host}/assets/img/404_notfound.jpg"

    response = make_response(json.dumps(response_body))
    response.headers["Content-Disposition"] = "inline; filename=check.json"
    response.mimetype = "application/json"

    return response

@app.route("/bokehro-resources")
def bokehro_resources():
    response_body = {
        "success": True,
        "js_files": CDN.js_files,
        "css_files": CDN.css_files
    }

    response = make_response(json.dumps(response_body))
    response.headers["Content-Disposition"] = "inline; filename=bokeh.json"
    response.mimetype = "application/json"

    return response

@app.route("/bokehro-export.<string:filetype>", methods=["GET", "POST"])
def bokehro_export(filetype: str = "json"):
    item_name: str            = request.args.get("name", default="", type=str)
    refinings: list[int]      = request.args.getlist("refining[]", type=int)

    card_enchants: list[str]  = request.args.getlist("card_enchant[]", type=str)
    random_options: list[str] = request.args.getlist("random_option[]", type=str)

    # init
    connection = None

    df = None

    if item_name is not None and item_name != "":
        try:
            connection = pymysql.connect(**args["mysql-ro"])

            query_item_trade: str = """
                SET STATEMENT max_statement_time=10
                FOR SELECT id, item_name, log_date, unit_price, world, map_name, refining_level, cards, random_options
                FROM item_trade_tbl
                WHERE item_name = %(item_name)s
            """

            refinings = [value for value in refinings if isinstance(value, int) == True]
            if len(refinings) > 0:
                query_item_trade += " AND refining_level IN({:s})".format(",".join(map(str, refinings)))

            if len(card_enchants) > 0:
                for value in card_enchants:
                    query_item_trade += " AND JSON_CONTAINS(cards, '\"{:s}\"', '$')".format(
                        connection.escape_string(value.replace("%","%%")))

            if len(random_options) > 0:
                for value in random_options:
                    query_item_trade += " AND JSON_CONTAINS(random_options, '\"{:s}\"', '$')".format(
                        connection.escape_string(value.replace("%","%%")))

            query_item_trade += " ORDER BY 1 ASC;"

            df = pd.read_sql(query_item_trade, connection, params={"item_name":item_name})

        except Exception as ex:
            raise ex
        finally:
            if connection is not None:
                connection.close()

    response = None
    if df is not None:
        df.set_index("id", inplace=True)
        buffer = StringIO()
        if filetype == "json":
            buffer.write(df.to_json())
            response = make_response(buffer.getvalue())
            response.headers["Content-Disposition"] = "attachment; filename=export.json"
            response.mimetype = "application/json"
        elif filetype == "csv":
            buffer.write(df.to_csv())
            response = make_response(buffer.getvalue())
            response.headers["Content-Disposition"] = "attachment; filename=export.csv"
            response.mimetype = "text/csv"
    return response

@app.route("/bokehro-items", methods=["GET"])
def bokehro_items():
    items: list = []

    try:
        connection = pymysql.connect(**args["mysql-ro"])

        query_string = """
            SET STATEMENT max_statement_time=10
            FOR SELECT item_name
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
