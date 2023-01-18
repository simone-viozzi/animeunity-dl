import requests
import argparse
import sys
import os
import json
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm

def parse_args():

    parser = argparse.ArgumentParser(
        description="AnimeUnity downloader"
    )

    parser.add_argument(
        "--url",
        help="The AnimeUnity URL",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--output",
        help="The output folder",
        type=str,
        required=False,
        default="./anime",
    )

    return parser.parse_args()


def main():

    args = parse_args()
    
    url = args.url
    output = args.output

    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")

    items = soup.findAll("video-player")

    if len(items) < 0:
        print("[-] Cannot fetch JSON data")
        exit(0)

    anime = json.loads(items[0]["anime"])
    title = anime["title"]
    title_eng = anime["title_eng"]

    folder = Path(output).joinpath(f"{title_eng} ({title})").resolve().absolute()

    folder.mkdir(parents=True, exist_ok=True)

    episodes = json.loads(items[0]["episodes"])

    for episode in tqdm(episodes, position=0):
        file_name = episode["file_name"]
        link = episode["link"]
        # download video
        r = requests.get(link, stream=True)
        with open(f"{folder}/{file_name}", "wb") as f:
            for chunk in tqdm(
                r.iter_content(chunk_size=1024),
                position=1,
                leave=True,
                desc=file_name,
                total=int(r.headers.get("content-length", 0)) // 1024,
                unit="KB",
            ):
                if chunk:
                    f.write(chunk)


if __name__ == "__main__":
    main()
