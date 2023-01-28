#!/usr/bin/env python3

import requests
import argparse
import sys
import os
import json
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
import re


def parse_args():

    parser = argparse.ArgumentParser(description="AnimeUnity downloader")

    parser.add_argument(
        "--url",
        help="The AnimeUnity URL",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--name",
        "-n",
        help="The anime name",
        type=str,
        required=False,
    )

    parser.add_argument(
        "--output",
        "-o",
        help="The output folder",
        type=str,
        required=False,
        default="./anime",
    )

    parser.add_argument(
        "--season",
        "-S",
        help="the season number",
        type=int,
        required=False,
        default=1,
    )

    parser.add_argument(
        "--episodes",
        "-E",
        help="the season number",
        type=str,
        required=False,
        default="all",
    )

    parser.add_argument(
        "--type",
        "-t",
        help="Film or anime",
        type=str,
        choices=["film", "anime", "f", "a"],
        required=False,
        default="anime",
    )

    args = parser.parse_args()

    if not args.output == "./anime":
        if not os.path.exists(args.output):
            print("[-] Output folder does not exists")
            sys.exit(0)
    
        if not os.path.isdir(args.output):
            print("[-] Output is not a folder")
            sys.exit(0)

    if args.type in ["f", "film"]:
        args.type = "film"

    if args.type in ["a", "anime"]:
        args.type = "anime"

    # episodes must me in the format "<10" or ">10" or "< 20"
    if args.episodes != "all" and not re.match(r"(<|>)\s?\d+", args.episodes):
        print("[-] Invalid episodes format")
        sys.exit(0)

    return args


def download_one(link, file_name, file_path, pbar_position=0):
    with requests.get(link, stream=True) as r:
        r.raise_for_status()
        size = int(r.headers.get("content-length", 0))

        if file_path.exists():
            if file_path.stat().st_size != size:
                tqdm.write(f"[!] {file_name} partially downloaded, removing")
                file_path.unlink()
            else:
                tqdm.write(f"[!] {file_name} already exists, skipping")
                return

        with open(file_path, "wb") as f, tqdm(
            position=pbar_position,
            leave=False,
            desc=file_name,
            unit="B",
            total=size,
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

    tqdm.write(f"[+] {file_name} downloaded")


def get_anime(video_metadata, basepath, season, episodes):
    folder = basepath / f"Season {season}"
    folder.mkdir(parents=True, exist_ok=True)

    episodes_list = json.loads(video_metadata[0]["episodes"])

    for episode in tqdm(episodes_list, position=0):

        ep = episode["number"]
        if episodes != "all":
            cond = f"{ep} {episodes}"
            print(cond)
            if not eval(cond):
                continue

        file_name = episode["file_name"].replace("_", " ")
        file_path = folder / file_name

        link = episode["link"]

        download_one(link, file_name, file_path, pbar_position=1)


def get_film(video_metadata, folder):
    folder.mkdir(parents=True, exist_ok=True)

    episodes = json.loads(video_metadata[0]["episodes"])

    film = episodes[0]

    file_name = film["file_name"].replace("_", " ")
    file_path = folder / file_name

    link = film["link"]

    download_one(link, file_name, file_path)


def main():

    args = parse_args()

    r = requests.get(args.url)
    soup = BeautifulSoup(r.content, "html.parser")

    video_metadata = soup.findAll("video-player")

    if len(video_metadata) < 0:
        print("[-] Cannot fetch JSON data")
        exit(0)

    anime = json.loads(video_metadata[0]["anime"])
    title_eng = anime["title_eng"].replace("(ITA)", "").strip()

    title = args.name or title_eng

    basepath = (Path(args.output) / title).resolve().absolute()

    if args.type == "anime":
        get_anime(video_metadata, basepath, args.season, args.episodes)
    elif args.type == "film":
        get_film(video_metadata, basepath)


if __name__ == "__main__":
    main()
