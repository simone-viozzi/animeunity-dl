#!/usr/bin/env python3

import requests
import argparse
import sys
import os
import json
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm


def parse_args():

    parser = argparse.ArgumentParser(description="AnimeUnity downloader")

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

    parser.add_argument(
        "-S",
        help="the season number",
        type=int,
        required=False,
        default=1,
    )

    return parser.parse_args()


def download_episode(request, file_name, file_path, size):
    with open(file_path, "wb") as f, tqdm(
        position=1,
        leave=False,
        desc=file_name,
        unit="B",
        total=size,
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for chunk in request.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))
        


def main():

    args = parse_args()

    url = args.url
    output = args.output
    season = args.S

    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")

    items = soup.findAll("video-player")

    if len(items) < 0:
        print("[-] Cannot fetch JSON data")
        exit(0)

    anime = json.loads(items[0]["anime"])
    title_eng = anime["title_eng"].replace("(ITA)", "").strip()

    folder = (Path(output) / title_eng / f"Season {season}").resolve().absolute()
    folder.mkdir(parents=True, exist_ok=True)

    episodes = json.loads(items[0]["episodes"])

    for episode in tqdm(episodes, position=0):
        file_name = episode["file_name"].replace("_", " ")
        file_path = folder / file_name

        link = episode["link"]
        with requests.get(link, stream=True) as r:
            r.raise_for_status()
            size = int(r.headers.get("content-length", 0))

            if file_path.exists():
                if file_path.stat().st_size != size:
                    tqdm.write(f"[!] {file_name} partially downloaded, removing")
                    file_path.unlink()
                else:
                    tqdm.write(f"[!] {file_name} already exists, skipping")
                    continue

            download_episode(r, file_name, file_path, size)

            tqdm.write(f"[+] {file_name} downloaded")


if __name__ == "__main__":
    main()
