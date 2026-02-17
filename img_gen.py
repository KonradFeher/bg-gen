import requests
import os
import sys
import json
import argparse
from io import BytesIO
from pprint import pprint
from datetime import datetime 
from PIL import Image, ImageFilter, ImageDraw

def add_shadow(background, foreground, blur_radius=20, shadow_opacity=160):
    padding = blur_radius * 3
    
    fg_w, fg_h = foreground.size
    
    shadow_alpha = Image.new("L", (fg_w + padding * 2, fg_h + padding * 2), 0)
    draw = ImageDraw.Draw(shadow_alpha)
    
    draw.rectangle(
        (padding, padding, padding + fg_w, padding + fg_h), 
        fill=shadow_opacity
    )

    shadow_alpha = shadow_alpha.filter(ImageFilter.GaussianBlur(blur_radius))

    shadow = Image.new("RGBA", shadow_alpha.size, (0, 0, 0, 0))
    shadow.putalpha(shadow_alpha)

    bg_w, bg_h = background.size
    x = (bg_w - fg_w) // 2
    y = (bg_h - fg_h) // 2
    
    shadow_pos = (x - padding, y - padding)
        
    background.paste(shadow, shadow_pos, shadow)
    background.paste(foreground, (x, y), foreground)

    return background


def gen_images(file_name, res=2560, out="output_images", limit=-1):
    limit = limit
    count = 0
    with open(file_name, "r") as f:
        records = json.load(f)

        for record in records:
            if limit > 0 and count > limit: break
            count += 1 
            # filename = (record["mbid"] if record["mbid"] != '' else (f"{record["artist"]}-{record["name"]}"))
            filename = f"{record["artist"]}-{record["name"]}"
            if os.path.exists("./output_images/" + filename + ".png"):
                print(f"{record["artist"]} - {record["name"]} exists already, skipping.")
                continue
            print(f"Generating {record["artist"]} - {record["name"]}")
            try:
                response = requests.get(record["image"], timeout=30)
                
                img = Image.open(BytesIO(response.content))
                img = img.convert("RGBA") 

                background = (
                    img
                    .filter(ImageFilter.GaussianBlur(10))
                    .resize((res, res), Image.LANCZOS)
                )
                foreground = img.copy().resize((res // 2, res // 2), Image.LANCZOS)

                x = (background.width - foreground.width) // 2
                y = (background.height - foreground.height) // 2

                add_shadow(background, foreground)
                background.save(f"{out}/{filename}.png", quality=95)
            except Exception as e:
                print(f"ERROR: {e} ")
                print("faulty image: " + record["image"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='img_gen.py', usage='%(prog)s --input <fetched_file.json> [options]')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=False, default='output_images')
    parser.add_argument('--limit', required=False, default=-1)
    parser.add_argument('--resolution', required=False, default=2560)
    args = parser.parse_args()
    gen_images(args.input)