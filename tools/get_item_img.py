#!/usr/bin/env python3

# pip3 install pyquery aiohttp Pillow

import argparse
import json
import os
import io
import traceback
import urllib.request, urllib.parse, urllib.error
from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser(description='')

parser.add_argument('--import-items',
                    action='store',
                    nargs='?',
                    default='./items.json',
                    type=str,
                    help='import items.json')

parser.add_argument('--export-path',
                    action='store',
                    nargs='?',
                    default='./images',
                    type=str,
                    help='export path')

parser.add_argument('--icon-url',
                    action='store',
                    nargs='?',
                    default='https://rotool.gungho.jp/icon/',
                    type=str,
                    help='icon url')

parser.add_argument('--font',
                    action='store',
                    nargs='?',
                    default='./SourceCodePro-Light.ttf',
                    type=str,
                    help='Font(TTF) file path')

args = parser.parse_args()

def download(args: dict, key: str, font: ImageFont):
    image_file_path = "{:s}/{:s}.png".format(args.export_path, key)
    if os.path.isfile(image_file_path) == True:
        print(key, "downloaded")
        return

    try:
        with urllib.request.urlopen("{:s}/{:s}.png".format(args.icon_url, key)) as response:
            data = response.read()

        # Pillowのイメージ化
        image = Image.open(io.BytesIO(data))
        # 横幅、高さ
        _, height = image.size
        draw = ImageDraw.Draw(image)
        draw.text((4,height-36), "(c)Gravity Co., Ltd. & LeeMyoungJin(studio DTDS) All rights reserved.\n(c)GungHo Online Entertainment, Inc. All Rights Reserved.", font=font)
        # 保存
        image.save(image_file_path, format="PNG", quality=100, optimize=True)

    except urllib.error.URLError as ex:
        print(key, ex)
    except:
        print(traceback.format_exc())
        raise

def main(args: dict):
    items = {}
    with open(args.import_items, "r", encoding="utf-8") as fp:
        items = json.load(fp)

    if os.path.isdir(args.export_path) == False:
        os.mkdir(args.export_path)

    font = ImageFont.truetype(args.font, size=10)
    for key in items:
        item = items[key]
        download(args, key, font)

if __name__ == '__main__':
    main(args)
