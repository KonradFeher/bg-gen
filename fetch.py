import requests
import dotenv
import os
import sys
import json
import jq
import argparse
from io import BytesIO
from pprint import pprint
from datetime import datetime 
from dotenv import load_dotenv, dotenv_values 
from PIL import Image, ImageFilter, ImageDraw

import img_gen

load_dotenv() 

root = 'http://ws.audioscrobbler.com/2.0'

params = {}
params['format'] = 'json'
params['api_key'] = os.getenv('api_key')
params['username'] = os.getenv('username')

os.makedirs("./output_images", exist_ok=True)

def from_csv(file):
    with open(file, 'r') as f:
        entries = f.readlines()

        info_responses = list()
        for entry in entries:
            search_params = dict(params)
            search_params['method'] = 'album.search'
            try:
                split = entry.split(' - ')
                artist = split[0]
                album = split[1]
                print(f'fetching: {artist} - {album}')
                search_params['artist'] = artist
                search_params['album'] = album
                r = requests.get(root, params=search_params)
                if r.status_code == 200:
                    results = r.json()

                    for m in results['results']['albummatches']['album']:
                        if m["image"][-1]["#text"] is not None and m["image"][-1]["#text"] != "":
                            info_responses.append({"mbid": m["mbid"], "image": m["image"][-1]["#text"].replace('300x300', '700x700'), "aritst": m['artist'], "name": m['name']})
                            break
                else: 
                    print(f'an error occured: {r.status_code}')
            except Exception as e:
                print(e)

        out = args.output
        with open(out, 'w') as f:
            f.write(json.dumps(info_responses))

    img_gen.gen_images(out)

def top_albums():
    top_params = dict(params)

    top_params['user'] = args.user
    top_params['limit'] = args.limit if 1000 > int(args.limit) > 0 else 1000
    top_params['period'] = 'overall' # maybe make this configurable
    top_params['method'] = 'user.getTopAlbums'

    info_responses = list()

    pages = 1
    for p in range(pages):
        top_params['page'] = p + 1

        r = requests.get(root, params=top_params)
        if r.status_code == 200:
            results = r.json()
            for a in results["topalbums"]["album"]:
                info_responses.append({
                    "mbid": a["mbid"],
                    "image": a["image"][-1]["#text"].replace('300x300', '0x0'),
                    "artist": a['artist']['name'],
                    "name": a['name']
                })
        
    with open(args.output, 'w') as f:
        f.write(json.dumps(info_responses))

if __name__=="__main__":
    parser = argparse.ArgumentParser(prog='fetch.py', usage='%(prog)s [options]')
    parser.add_argument('--user', required=False)
    parser.add_argument('--limit', required=False, default=1000)
    parser.add_argument('--file', required=False)
    parser.add_argument('--output', required=False, default=('output/' + str(datetime.now().timestamp()) + '.json'))
    parser.add_argument('--gen', action='store_true')
    args = parser.parse_args()

    if args.user is not None:    
        top_albums()
    elif args.file is not None:
        from_csv()
    else: print("Invalid/missing args.")

    if args.gen:
        print("Fetch done. Generating images.")
        img_gen.gen_images(args.output)