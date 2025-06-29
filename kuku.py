import argparse
import json
import os
import re
import requests
from mutagen.mp4 import MP4, MP4Cover
from urllib.parse import urlparse
import yt_dlp
from http.cookiejar import MozillaCookieJar


TITLE = "\r\n /$$   /$$           /$$                               /$$ /$$\r\n| $$  /$$/          | $$                              | $$| $$\r\n| $$ /$$/  /$$   /$$| $$   /$$ /$$   /$$          /$$$$$$$| $$\r\n| $$$$$/  | $$  | $$| $$  /$$/| $$  | $$ /$$$$$$ /$$__  $$| $$\r\n| $$  $$  | $$  | $$| $$$$$$/ | $$  | $$|______/| $$  | $$| $$\r\n| $$\\  $$ | $$  | $$| $$_  $$ | $$  | $$        | $$  | $$| $$\r\n| $$ \\  $$|  $$$$$$/| $$ \\  $$|  $$$$$$/        |  $$$$$$$| $$\r\n|__/  \\__/ \\______/ |__/  \\__/ \\______/          \\_______/|__/\r\n                      --by @bunnykek"

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8,it-IT;q=0.7,it;q=0.6',
    'cache-control': 'no-cache',
    'dnt': '1',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
}


class KuKu:
    def __init__(self, url: str) -> None:
        """
        __init__()

        initializes a session to be used to recieve API data from KukuFM.
        """
        self.showID = urlparse(url).path.split('/')[-1]
        self.session = requests.Session()
        cookie_jar = MozillaCookieJar('cookies.txt')
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        self.session.headers.update(HEADERS)
        self.session.cookies.update(cookie_jar)

        response = self.session.get(
            f"https://kukufm.com/api/v2.3/channels/{self.showID}/episodes/?page=1")
        data = response.json()

        show: dict = data['show']
        # print(show)
        self.metadata = {
            'title': KuKu.sanitiseName(show['title'].strip()),
            'image': show['original_image'],
            'date': show['published_on'],
            'fictional': show['is_fictional'],
            'nEpisodes': show['n_episodes'],
            'author': show['author']['name'].strip(),
            'lang': show['language'].capitalize().strip(),
            'type': ' '.join(show['content_type']['slug'].strip().split('-')).capitalize(),
            'ageRating': show.get('meta_data', {}).get('age_rating', None),
            'credits': {},
            'hasVideoEps': "video_thumbnail" in show["other_images"]
        }

        album_info = F"""Album info:
                Name       : {self.metadata['title']}                  
                Author     : {self.metadata['author']}
                Language   : {self.metadata['lang']}
                Date       : {self.metadata['date']}
                Age rating : {self.metadata['ageRating']}
                Episodes   : {self.metadata['nEpisodes']}
                Video Eps  : {self.metadata['hasVideoEps']}
        """

        print(album_info)

        for credit in show['credits'].keys():
            self.metadata['credits'][credit] = ', '.join(
                [person['full_name'] for person in show['credits'][credit]])

    @staticmethod
    def sanitiseName(name) -> str:
        return re.sub(r'[:]', ' - ', re.sub(r'[\\/*?"<>|$]', '', re.sub(r'[ \t]+$', '', str(name).rstrip())))

    def downloadAndTag(self, episodeMetadata: dict, path: str, srtPath: str, coverPath: str) -> None:
        """
        downloadAndTag()

        Method to download and tag locally using the KukuFM API and FFMPEG

        @param episodeMetadata: dict object that includes the track metadata.
        @param path: str which sets a path to be downloaded to.
        @param srtPath: str which sets the subtitle file path.
        @param coverPath: str path which locates where cover art is, so it'll be embeded within the file.
        """
        print('Downloading', episodeMetadata['title'], flush=True)
        if os.path.exists(path):
            print(episodeMetadata['title'], 'already exists!', flush=True)
            return

        ydl_opts = {
            'format': 'best',
            'outtmpl': path,
            'http_headers': HEADERS,
            'quiet': True,
            'no_warnings': True,
            'cookiefile': "cookies.txt",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([episodeMetadata['url']])

        hasLyrics: bool = len(episodeMetadata['srt'])

        if hasLyrics:
            srt_response = self.session.get(episodeMetadata['srt'])
            with open(srtPath, 'w', encoding='utf-8') as f:
                f.write(srt_response.text)

        tag = MP4(path)

        # if hasLyrics:
        #     tag['\xa9lyr'] = [KuKu.srt_to_custom_format(srt_response.text)]
        tag['\xa9alb'] = [self.metadata['title']]
        tag['\xa9ART'] = [self.metadata['author']]
        tag['aART'] = [self.metadata['author']]
        tag['\xa9day'] = [episodeMetadata['date'][0:10]]
        tag['trkn'] = [(int(episodeMetadata['epNo']),
                        int(self.metadata['nEpisodes']))]
        tag['stik'] = [2]
        tag['\xa9nam'] = [episodeMetadata['title']]
        tag.pop("©too")

        tag['----:com.apple.iTunes:Fictional'] = bytes(
            str(self.metadata["fictional"]), 'UTF-8')
        tag['----:com.apple.iTunes:Author'] = bytes(
            str(self.metadata["author"]), 'UTF-8')
        tag['----:com.apple.iTunes:Language'] = bytes(
            str(self.metadata["lang"]), 'UTF-8')
        tag['----:com.apple.iTunes:Type'] = bytes(
            str(self.metadata["type"]), 'UTF-8')
        tag['----:com.apple.iTunes:Season'] = bytes(
            str(episodeMetadata["seasonNo"]), 'UTF-8')
        if self.metadata["ageRating"]:
            tag['----:com.apple.iTunes:Age rating'] = bytes(
                str(self.metadata["ageRating"]), 'UTF-8')

        for cat in self.metadata['credits'].keys():
            credit = cat.replace('_', ' ').capitalize()
            tag[f'----:com.apple.iTunes:{credit}'] = bytes(
                str(self.metadata['credits'][cat]), 'UTF-8')
        with open(coverPath, 'rb') as f:
            pic = MP4Cover(f.read())
            tag['covr'] = [pic]
        tag.save()

    def downAlbum(self) -> None:
        """
        downAlbum()

        Method where it'll prepare a storyID to be stored onto locally.
        """
        folderName = f"{self.metadata['title']} "
        folderName += f"({self.metadata['date'][:4]}) " if self.metadata.get(
            'date') else ''
        folderName += f"[{self.metadata['lang']}]"

        albumPath = os.path.join(
            os.getcwd(), 'Downloads', self.metadata['lang'], self.metadata['type'], self.sanitiseName(folderName))

        if not os.path.exists(albumPath):
            os.makedirs(albumPath)

        with open(os.path.join(albumPath, 'cover.png'), 'wb') as f:
            f.write(self.session.get(self.metadata['image']).content)

        episodes = []
        page = 1

        while True:
            response = self.session.get(
                f'https://kukufm.com/api/v2.3/channels/{self.showID}/episodes/?page={page}')
            data = response.json()
            episodes.extend(data["episodes"])
            page += 1

            if not data["has_more"]:
                break

        for ep in episodes:
            epMeta = {
                'title': KuKu.sanitiseName(ep["title"].strip()),
                'url': ep['content']['hls_url'].strip(),
                'srt': ep['content'].get('subtitle_url', "").strip(),
                'epNo': ep['index'],
                'seasonNo': ep['season_no'],
                'date': str(ep.get('published_on')).strip(),
            }
            # print(ep['content']['hls_url'])
            # print(epMeta)

            trackPath = os.path.join(
                albumPath, f"{str(ep['index']).zfill(2)}. {epMeta['title']}.{'mp4' if self.metadata['hasVideoEps'] else 'm4a'}")
            srtPath = os.path.join(
                albumPath, f"{str(ep['index']).zfill(2)}. {epMeta['title']}.srt")
            self.downloadAndTag(epMeta, trackPath, srtPath,
                                os.path.join(albumPath, 'cover.png'))


if __name__ == '__main__':
    print(TITLE)
    parser = argparse.ArgumentParser(
        prog='kuku-dl',
        description='KuKu FM Downloader!',
    )
    parser.add_argument('url', help="Show Url")
    args = parser.parse_args()
    KuKu(args.url).downAlbum()
