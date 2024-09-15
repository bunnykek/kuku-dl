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
import shutil
import warnings
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from traceback import format_exc
from urllib.parse import urlparse

import aiofiles
import aiohttp
import requests
from mutagen.mp4 import MP4, MP4Cover
from yt_dlp import YoutubeDL, utils

from .errors import UnableToArchive, EpisodeNotFound, UnableToDownload
from .logger import LOGS

# TODO: Option to Combine The Audios Into One Audio File

class KuKu:
    def __init__(
        self,
        url: str,
        path: str = "downloads",
        rip_subtitles: bool = False,
        batch_size: int = 5,
        archive: bool = False,
    ):
        LOGS.info("Initializing Your Request...")
        self.batch_size = batch_size
        self._path = path
        self.rip_subs = rip_subtitles
        self.archive = archive
        self.showID = urlparse(url).path.split("/")[-1]
        self.session = aiohttp.ClientSession()
        data = requests.get(
            f"https://kukufm.com/api/v2.3/channels/{self.showID}/episodes/?page=1"
        ).json()
        show = data["show"]
        self.metadata = {
            "title": self._sanitiseName(show["title"].strip()),
            "image": show["original_image"],
            "date": show["published_on"],
            "fictional": show["is_fictional"],
            "nEpisodes": show["n_episodes"],
            "author": show["author"]["name"].strip(),
            "lang": show["language"].capitalize().strip(),
            "type": " ".join(
                show["content_type"]["slug"].strip().split("-")
            ).capitalize(),
            "ageRating": show["meta_data"].get("age_rating"),
            "credits": {},
        }
        self.opts = {
            "format": "best",
            "addmetadata": True,
            "key": "FFmpegMetadata",
            "prefer_ffmpeg": True,
            "geo_bypass": True,
            "logtostderr": False,
            "no_warnings": True,
            "logger": LOGS
        }
        self._create_dirs()
        LOGS.info("Successfully Initialized Your Request!!!")

    @staticmethod
    def _run_async(function):
        @wraps(function)
        async def wrapper(*args, **kwargs):
            return await asyncio.get_event_loop().run_in_executor(
                ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() * 5),
                partial(function, *args, **kwargs),
            )

        return wrapper

    @_run_async
    def hls_download(self, url, opts):
        try:
            return YoutubeDL(opts).download([url])
        except utils.DownloadError:
            if "128kb.m3u8" in url.strip():
                url = url.strip()[:-10] + ".m3u8"
                return YoutubeDL(opts).download([url])
            raise UnableToDownload(f"Unable To Download {url}")
        except BaseException:
            LOGS.error(str(format_exc()))

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

    def _divide_list(self, lst, n):
        k, m = divmod(len(lst), n)
        return [lst[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n)]

    async def _get_response(self, url) -> dict:
        res = await self.session.get(url)
        return await res.json()

    async def _get_srt(self, url) -> str:
        res = await self.session.get(url)
        return await res.text()

    def _sanitiseName(self, name) -> str:
        return re.sub(
            r"[:]",
            " - ",
            re.sub(r'[\\/*?"<>|$]', "", re.sub(r"[ \t]+$", "", str(name).rstrip())),
        )

    def _create_zip(self):
        LOGS.info("Archiving The Album...")
        shutil.make_archive(self.albumPath, "zip", self.albumPath)
        zip_path = self.albumPath + ".zip"
        if os.path.exists(zip_path):
            shutil.rmtree(self.albumPath)
            LOGS.info("Successfully Archived The Album!")
            return zip_path
        raise UnableToArchive("Unable To Archive The Album!")

    def _create_dirs(self) -> None:
        folderName = f"{self.metadata['title']} "
        folderName += (
            f"({self.metadata['date'][:4]}) " if self.metadata.get("date") else ""
        )
        folderName += f"[{self.metadata['lang']}]"
        self.albumPath = os.path.join(
            os.getcwd(), self._path, self._sanitiseName(folderName)
        )
        if not os.path.exists(self.albumPath):
            os.makedirs(self.albumPath)
        self.cover = os.path.join(self.albumPath, "cover.png")
        with open(self.cover, "wb") as f:
            f.write(requests.get(self.metadata["image"]).content)

    async def _download(self, episodeMetadata: dict, path: str, srtPath: str) -> None:
        if os.path.exists(path):
            return
        opts = dict(self.opts)
        opts["outtmpl"] = path

        LOGS.info(f"Downloading '{episodeMetadata['title']}' ...")

        try:
            await self.hls_download(url=episodeMetadata["hls"], opts=opts)
        except UnableToDownload as UDE:
            LOGS.warning(UDE)
            return 

        hasLyrics: bool = len(episodeMetadata["srt"])
        if hasLyrics and srtPath:
            srt_response = await self._get_srt(episodeMetadata["srt"])
            async with aiofiles.open(srtPath, "w", encoding="utf-8") as f:
                await f.write(srt_response)

        tag = MP4(path)

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
        if self.metadata["ageRating"]:
            tag['----:com.apple.iTunes:Age rating'] = bytes(
                str(self.metadata["ageRating"]), 'UTF-8')

        for cat in self.metadata["credits"].keys():
            credit = cat.replace("_", " ").capitalize()
            tag[f"----:com.apple.iTunes:{credit}"] = bytes(
                str(self.metadata["credits"][cat]), "UTF-8"
            )
        async with aiofiles.open(self.cover, "rb") as f:
            pic = MP4Cover(await f.read())
            tag["covr"] = [pic]
        tag.save()
        LOGS.info(f"Successfully Downloaded '{episodeMetadata['title']}' !")

    async def downloadAlbum(self) -> str:
        episodes = []
        page = 1
        tasks = []

        while True:
            data = await self._get_response(
                f"https://kukufm.com/api/v2.0/channels/{self.showID}/episodes/?page={page}"
            )
            episodes.extend(data["episodes"])
            page += 1
            if not data["has_more"]:
                break

        for ep in episodes:
            epMeta = {
                "title": self._sanitiseName(ep["title"].strip()),
                "hls": ep["content"]["hls_url"].strip()[:-5] + "128kb.m3u8" if ep["content"].get("hls_url") else None,
                "srt": ep["content"].get("subtitle_url", "").strip(),
                "epNo": ep["index"],
                "seasonNo": ep["season_no"],
                "date": str(ep.get("published_on")).strip(),
            }
            if not epMeta["hls"]:
                LOGS.warning(f"Unable To Rip '{epMeta['title']}' , Skipping!")
                continue
            trackPath = os.path.join(self.albumPath, f"{epMeta['title']}.m4a")
            srtPath = (
                os.path.join(self.albumPath, f"{epMeta['title']}.srt")
                if self.rip_subs
                else None
            )
            tasks.append(self._download(epMeta, trackPath, srtPath))

        await self._divide_and_run(tasks)
        await self.session.close()
        if self.archive:
            return self._create_zip()
        return self.albumPath

    # i tried episode endpoint but it didn't give hls url, so have to use the following approach
    async def downloadEpisode(self, episode: int, season: int = 1) -> str:
        page = 1

        while True:
            data = await self._get_response(
                f"https://kukufm.com/api/v2.0/channels/{self.showID}/episodes/?page={page}"
            )
            for ep in data["episodes"]:
                epMeta = {
                    "title": self._sanitiseName(ep["title"].strip()),
                    "hls": ep["content"]["hls_url"].strip()[:-5] + "128kb.m3u8" if ep["content"].get("hls_url") else None,
                    "srt": ep["content"].get("subtitle_url", "").strip(),
                    "epNo": int(ep["index"]),
                    "seasonNo": int(ep["season_no"]),
                    "date": str(ep.get("published_on")).strip(),
                }
                if epMeta["epNo"] == episode and epMeta["seasonNo"] == season:
                    if not epMeta["hls"]:
                        LOGS.critical(f"Unable To Rip '{epMeta['title']}' !")
                        return
                    trackPath = os.path.join(self.albumPath, f"{epMeta['title']}.m4a")
                    srtPath = (
                        os.path.join(self.albumPath, f"{epMeta['title']}.srt")
                        if self.rip_subs
                        else None
                    )
                    await self._download(epMeta, trackPath, srtPath)
                    await self.session.close()
                    if self.archive:
                        return self._create_zip()
                    return self.albumPath
            page += 1
            if not data["has_more"]:
                break
        raise EpisodeNotFound("Unable To Find The Following Episode")

    async def _divide_and_run(self, tasks: list) -> None:
        tasks = self._divide_list(tasks, self.batch_size)
        for task_batch in tasks:
            await asyncio.gather(*task_batch)
            await asyncio.sleep(2)