#    This file is part of the kuku-dl distribution.
#    Copyright (c) 2024 bunnykek
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License for more details.
#
# License can be found in <
# https://github.com/bunnykek/kuku-dl/blob/main/LICENSE > .

# if you are using this following code then don't forgot to give proper
# credit to (github.com/bunnykek)

import asyncio
import multiprocessing
import os
import re
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from traceback import format_exc
from urllib.parse import urlparse

import aiofiles
import aiohttp
import requests
from mutagen.mp4 import MP4, MP4Cover
from yt_dlp import YoutubeDL

# TODO: Replace Print With Logging And Adding Zip Option And Combine
# Option And GPLv3 in Repo


class Formats:
    HIGHEST = "320"
    MEDIUM = "256"
    LOWEST = "128"


class KuKu:
    def __init__(
        self,
        url: str,
        formats=Formats.LOWEST,
        path: str = "downloads",
        rip_subtitles: bool = False,
        batch_size: int = 5,
    ):
        self.batch_size = batch_size
        self._path = path
        self.rip_subs = rip_subtitles
        self.showID = urlparse(url).path.split("/")[-1]
        self.session = aiohttp.ClientSession()
        data = requests.get(
            f"https://kukufm.com/api/v2.3/channels/{self.showID}/episodes/?page=1"
        ).json()
        show = data["show"]
        self.metadata = {
            "title": self.sanitiseName(show["title"].strip()),
            "image": show["original_image"],
            "date": show["published_on"],
            "fictional": show["is_fictional"],
            "nEpisodes": show["n_episodes"],
            "author": show["author"]["name"].strip(),
            "lang": show["language"].capitalize().strip(),
            "type": " ".join(
                show["content_type"]["slug"].strip().split("-")
            ).capitalize(),
            "ageRating": show["meta_data"]["age_rating"].strip(),
            "credits": {},
        }
        self.opts = {
            "format": "best",
            "addmetadata": True,
            "key": "FFmpegMetadata",
            "prefer_ffmpeg": True,
            "geo_bypass": True,
            "logtostderr": False,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                    "preferredquality": formats,
                },
                {"key": "FFmpegMetadata"},
            ],
        }
        self.create_dirs()

    @staticmethod
    def run_async(function):
        @wraps(function)
        async def wrapper(*args, **kwargs):
            return await asyncio.get_event_loop().run_in_executor(
                ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() * 5),
                partial(function, *args, **kwargs),
            )

        return wrapper

    @run_async
    def hls_download(self, url, opts):
        try:
            return YoutubeDL(opts).download([url])
        except BaseException:
            print(format_exc())

    @property
    def album_info(self) -> dict:
        return {
            "name": self.metadata["title"],
            "author": self.metadata["author"],
            "language": self.metadata["lang"],
            "date": self.metadata["date"],
            "age_rating": self.metadata["ageRating"],
            "episodes": self.metadata["nEpisodes"],
        }

    def divide_list(self, lst, n):
        k, m = divmod(len(lst), n)
        return [lst[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n)]

    async def get_response(self, url) -> dict:
        res = await self.session.get(url)
        return await res.json()

    async def get_srt(self, url) -> str:
        res = await self.session.get(url)
        return await res.text()

    def sanitiseName(self, name) -> str:
        return re.sub(
            r"[:]",
            " - ",
            re.sub(r'[\\/*?"<>|$]', "", re.sub(r"[ \t]+$", "", str(name).rstrip())),
        )

    def create_dirs(self) -> None:
        folderName = f"{self.metadata['title']} "
        folderName += (
            f"({self.metadata['date'][:4]}) " if self.metadata.get("date") else ""
        )
        folderName += f"[{self.metadata['lang']}]"
        self.albumPath = os.path.join(
            os.getcwd(), self._path, self.sanitiseName(folderName)
        )
        if not os.path.exists(self.albumPath):
            os.makedirs(self.albumPath)
        self.cover = os.path.join(self.albumPath, "cover.png")
        with open(self.cover, "wb") as f:
            f.write(requests.get(self.metadata["image"]).content)

    async def download(self, episodeMetadata: dict, path: str, srtPath: str) -> None:
        if os.path.exists(path):
            print(episodeMetadata["title"], "Already Exists!", flush=True)
            return
        opts = dict(self.opts)
        opts["outtmpl"] = path
        await self.hls_download(url=episodeMetadata["hls"], opts=opts)

        hasLyrics: bool = len(episodeMetadata["srt"])
        if hasLyrics and srtPath:
            srt_response = await self.get_srt(episodeMetadata["srt"])
            async with aiofiles.open(srtPath, "w", encoding="utf-8") as f:
                await f.write(srt_response)

        tag = MP4(path + ".m4a")

        tag["\xa9alb"] = [self.metadata["title"]]
        tag["\xa9ART"] = [self.metadata["author"]]
        tag["aART"] = [self.metadata["author"]]
        tag["\xa9day"] = [episodeMetadata["date"][0:10]]
        tag["trkn"] = [(int(episodeMetadata["epNo"]), int(self.metadata["nEpisodes"]))]
        tag["stik"] = [2]
        tag["\xa9nam"] = [episodeMetadata["title"]]

        if "©too" in tag:
            tag.pop("©too")

        tag["----:com.apple.iTunes:Fictional"] = bytes(
            str(self.metadata["fictional"]), "UTF-8"
        )
        tag["----:com.apple.iTunes:Author"] = bytes(
            str(self.metadata["author"]), "UTF-8"
        )
        tag["----:com.apple.iTunes:Language"] = bytes(
            str(self.metadata["lang"]), "UTF-8"
        )
        tag["----:com.apple.iTunes:Type"] = bytes(str(self.metadata["type"]), "UTF-8")
        tag["----:com.apple.iTunes:Season"] = bytes(
            str(episodeMetadata["seasonNo"]), "UTF-8"
        )
        tag["----:com.apple.iTunes:Age rating"] = bytes(
            str(self.metadata["ageRating"]), "UTF-8"
        )

        for cat in self.metadata["credits"].keys():
            credit = cat.replace("_", " ").capitalize()
            tag[f"----:com.apple.iTunes:{credit}"] = bytes(
                str(self.metadata["credits"][cat]), "UTF-8"
            )
        async with aiofiles.open(self.cover, "rb") as f:
            pic = MP4Cover(await f.read())
            tag["covr"] = [pic]
        tag.save()

    async def downloadAlbum(self) -> str:
        episodes = []
        page = 1
        tasks = []

        while True:
            data = await self.get_response(
                f"https://kukufm.com/api/v2.0/channels/{self.showID}/episodes/?page={page}"
            )
            episodes.extend(data["episodes"])
            page += 1
            if not data["has_more"]:
                break

        for ep in episodes:
            epMeta = {
                "title": self.sanitiseName(ep["title"].strip()),
                "hls": ep["content"]["hls_url"].strip()[:-5] + "128kb.m3u8",
                "srt": ep["content"].get("subtitle_url", "").strip(),
                "epNo": ep["index"],
                "seasonNo": ep["season_no"],
                "date": str(ep.get("published_on")).strip(),
            }
            trackPath = os.path.join(self.albumPath, f"{epMeta['title']}")
            srtPath = (
                os.path.join(self.albumPath, f"{epMeta['title']}.srt")
                if self.rip_subs
                else None
            )
            tasks.append(self.download(epMeta, trackPath, srtPath))

        await self.divide_and_run(tasks)
        await self.session.close()
        return self.albumPath

    async def divide_and_run(self, tasks: list) -> None:
        tasks = self.divide_list(tasks, self.batch_size)
        for task_batch in tasks:
            asyncio.gather(*task_batch)
            await asyncio.sleep(5)
