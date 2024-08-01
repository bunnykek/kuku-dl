import argparse, os, re, requests
import aiohttp, aiofiles, asyncio, multiprocessing
from yt_dlp import YoutubeDL
from mutagen.flac import FLAC, Picture
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from traceback import format_exc

class Formats:
    HIGHEST = "320"
    MEDIUM = "256"
    LOWEST = "128"

class KuKu:
    def __init__(self, url: str, formats=Formats.LOWEST, path: str="downloads",rip_subtitles: bool=False, workers: int=5):
        self.workers = workers
        self._path = path
        self.rip_subs = rip_subtitles
        self.showID = urlparse(url).path.split('/')[-1]
        self.session = aiohttp.ClientSession()
        data = requests.get(f"https://kukufm.com/api/v2.3/channels/{self.showID}/episodes/?page=1").json()
        show = data['show']
        self.metadata = {
            'title': self.sanitiseName(show['title'].strip()),
            'image': show['original_image'],
            'date': show['published_on'],
            'fictional': show['is_fictional'],
            'nEpisodes': show['n_episodes'],
            'author': show['author']['name'].strip(),
            'lang': show['language'].capitalize().strip(),
            'type': ' '.join(show['content_type']['slug'].strip().split('-')).capitalize(),
            'ageRating': show['meta_data']['age_rating'].strip(),
            'credits': {},
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
                    "preferredcodec": "flac",
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
            "name": self.metadata['title'],
            "author": self.metadata['author'],
            "language": self.metadata['lang'],
            "date": self.metadata['date'],
            "age_rating": self.metadata['ageRating'],
            "episodes": self.metadata['nEpisodes']
        }

    def divide_list(self, lst, n):
        k, m = divmod(len(lst), n)
        return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]

    async def get_response(self, url) -> dict:
        res = await self.session.get(url)
        return await res.json()

    async def get_srt(self, url) -> str:
        res = await self.session.get(url)
        return await res.text()

    def sanitiseName(self, name) -> str:
        return re.sub(r'[:]', ' - ', re.sub(r'[\\/*?"<>|$]', '', re.sub(r'[ \t]+$', '', str(name).rstrip())))

    def create_dirs(self) -> None:
        folderName = f"{self.metadata['title']}"
        folderName += f"({self.metadata['date'][:4]}) " if self.metadata.get(
            'date') else ''
        folderName += f"[{self.metadata['lang']}]"
        self.albumPath = os.path.join(
            os.getcwd(), self._path, self.sanitiseName(folderName))
        if not os.path.exists(self.albumPath):
            os.makedirs(self.albumPath)
        self.cover = os.path.join(self.albumPath, 'cover.png')
        with open(self.cover, 'wb') as f:
            f.write(requests.get(self.metadata['image']).content)

    async def download(self, episodeMetadata: dict, path: str, srtPath: str) -> None:
        if os.path.exists(path):
            print(episodeMetadata['title'], 'Already Exists!', flush=True)
            return
        opts = dict(self.opts)
        opts["outtmpl"] = path
        await self.hls_download(url=episodeMetadata['hls'], opts=opts)

        hasLyrics: bool = len(episodeMetadata['srt'])
        if hasLyrics and srtPath:
            srt_response = await self.get_srt(episodeMetadata['srt'])
            async with aiofiles.open(srtPath, 'w', encoding='utf-8') as f:
                await f.write(srt_response)

        tag = FLAC(path+".flac")
        
        tag['album'] = self.metadata['title']
        tag['artist'] = self.metadata['author']
        tag['albumartist'] = self.metadata['author']
        tag['date'] = episodeMetadata['date'][0:10]
        tag['tracknumber'] = str(episodeMetadata['epNo'])
        tag['totaltracks'] = str(self.metadata['nEpisodes'])
        tag['title'] = episodeMetadata['title']
        tag['description'] = "Fictional" if self.metadata["fictional"] else ""

        tag['author'] = self.metadata["author"]
        tag['language'] = self.metadata["lang"]
        tag['type'] = self.metadata["type"]
        tag['season'] = str(episodeMetadata["seasonNo"])
        tag['age_rating'] = str(self.metadata["ageRating"])

        for cat in self.metadata['credits'].keys():
            credit = cat.replace('_', ' ').capitalize()
            tag[credit] = self.metadata['credits'][cat]

        async with aiofiles.open(self.cover, 'rb') as f:
            pic = Picture()
            pic.data = await f.read()
            pic.type = 3
            pic.mime = "image/png"
            tag.add_picture(pic)
        tag.save()

    async def downloadAlbum(self) -> str:
        episodes = []
        page = 1
        tasks = []

        while True:
            data = await self.get_response(f'https://kukufm.com/api/v2.0/channels/{self.showID}/episodes/?page={page}')
            episodes.extend(data["episodes"])
            page += 1
            if not data["has_more"]:
                break

        for ep in episodes:
            epMeta = {
                'title': self.sanitiseName(ep["title"].strip()),
                'hls': ep['content']['hls_url'].strip()[:-5]+"128kb.m3u8",
                'srt': ep['content'].get('subtitle_url', "").strip(),
                'epNo': ep['index'],
                'seasonNo': ep['season_no'],
                'date': str(ep.get('published_on')).strip(),
            }
            trackPath = os.path.join(
                self.albumPath, f"{epMeta['title']}")
            srtPath = os.path.join(self.albumPath, f"{epMeta['title']}.srt") if self.rip_subs else None
            tasks.append(self.download(epMeta, trackPath, srtPath))

        await self.divide_and_run(tasks)
        await self.session.close()
        return self.albumPath

    async def divide_and_run(self, tasks: list) -> None:
        tasks = self.divide_list(tasks, self.workers)
        for task_batch in tasks:
            asyncio.gather(*task_batch)
            await asyncio.sleep(10)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='kuku-dl', description='KuKu FM Downloader!',)

    parser.add_argument('url', type=str, help='The URL of the video to download')
    parser.add_argument('--formats', choices=[Formats.HIGHEST, Formats.MEDIUM, Formats.LOWEST], default=Formats.LOWEST, help='The format to download the audio in (default: 128)')
    parser.add_argument('--path', type=str, default='downloads', help='The path to save the Album (default: downloads)')
    parser.add_argument('--rip-subtitles', action='store_true', default=False, help='Whether to rip subtitles (default: False)')
    parser.add_argument('--workers', type=int, default=5, help='Number of worker threads to use (default: 5)')

    args = parser.parse_args()
    KUKU = KuKu(args.url, args.formats, args.path, args.rip_subtitles, args.workers)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(KUKU.downloadAlbum())
