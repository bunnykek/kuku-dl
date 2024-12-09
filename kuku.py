import argparse
import json
import os
import re
import requests
import subprocess
from mutagen.mp4 import MP4, MP4Cover
from urllib.parse import urlparse

TITLE = "\r\n /$$   /$$           /$$                               /$$ /$$\r\n| $$  /$$/          | $$                              | $$| $$\r\n| $$ /$$/  /$$   /$$| $$   /$$ /$$   /$$          /$$$$$$$| $$\r\n| $$$$$/  | $$  | $$| $$  /$$/| $$  | $$ /$$$$$$ /$$__  $$| $$\r\n| $$  $$  | $$  | $$| $$$$$$/ | $$  | $$|______/| $$  | $$| $$\r\n| $$\\  $$ | $$  | $$| $$_  $$ | $$  | $$        | $$  | $$| $$\r\n| $$ \\  $$|  $$$$$$/| $$ \\  $$|  $$$$$$/        |  $$$$$$$| $$\r\n|__/  \\__/ \\______/ |__/  \\__/ \\______/          \\_______/|__/\r\n                      --by @bunnykek"

class KuKu:
    def __init__(self, url: str) -> None:
        """
        __init__()

        initializes a session to be used to recieve API data from KukuFM.
        """
        self.showID = urlparse(url).path.split('/')[-1]
        self.session = requests.Session()

        response = self.session.get(f"https://kukufm.com/api/v2.3/channels/{self.showID}/episodes/?page=1")
        data = response.json()

        show = data['show']
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
            'ageRating': show['meta_data'].get('age_rating', None),
            'credits': {},
        }

        album_info = F"""Album: {self.metadata['title']} ({self.metadata['nEpisodes']} episodes)
Author: {self.metadata['author']} | Language: {self.metadata['lang']}"""
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
        print(f"\rDownloading: {episodeMetadata['title']}", end='', flush=True)
        if os.path.exists(path):
            print(f"\rSkipped: {episodeMetadata['title']} (already exists)", flush=True)
            return

        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Download using ffmpeg
        audio_url = episodeMetadata['hls']
        
        # Don't modify the URL if it already contains m3u8
        if not audio_url.endswith('m3u8'):
            if audio_url.endswith('/'):
                audio_url = audio_url.rstrip('/') + "/128kb.m3u8"
            else:
                audio_url = audio_url + "/128kb.m3u8"
            
        result = subprocess.run(['ffmpeg', '-i', audio_url,
                      '-c', 'copy', '-y', '-hide_banner', '-loglevel', 'error', path],
                      capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"\rError: Failed to download {episodeMetadata['title']}")
            if result.stderr:
                print(f"Error details: {result.stderr}")
            return
        
        print(f"\rCompleted: {episodeMetadata['title']}", flush=True)
        
        hasLyrics: bool = len(episodeMetadata['srt'])
        
        if hasLyrics:
            srt_response = self.session.get(episodeMetadata['srt'])
            with open(srtPath, 'w', encoding='utf-8') as f:
                f.write(srt_response.text)
        
        tag = MP4(path)
        
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

        # Use current directory instead of getcwd()
        albumPath = os.path.join(
            'Downloads', self.metadata['lang'], self.metadata['type'], self.sanitiseName(folderName))

        # Create all directories in the path
        os.makedirs(albumPath, exist_ok=True)

        coverPath = os.path.join(albumPath, 'cover.png')
        with open(coverPath, 'wb') as f:
            f.write(self.session.get(self.metadata['image']).content)

        episodes = []
        page = 1

        while True:
            response = self.session.get(
                f'https://kukufm.com/api/v2.0/channels/{self.showID}/episodes/?page={page}')
            data = response.json()
            episodes.extend(data["episodes"])
            page += 1
            
            if not data["has_more"]:
                break

        for ep in episodes:
            # Get the audio URL, preferring premium_audio_url over hls_url
            audio_url = ep['content'].get('premium_audio_url', '') or ep['content'].get('hls_url', '')
            audio_url = audio_url.strip()
            
            if not audio_url:
                print(f"\rError: No audio URL found for episode {ep['title']}")
                continue
                
            epMeta = {
                'title': KuKu.sanitiseName(ep["title"].strip()),
                'hls': audio_url,
                'srt': ep['content'].get('subtitle_url', "").strip(),
                'epNo': ep['index'],
                'seasonNo': ep['season_no'],
                'date': str(ep.get('published_on')).strip(),
            }
                        
            trackPath = os.path.join(
                albumPath, f"{str(ep['index']).zfill(2)}. {epMeta['title']}.m4a")
            srtPath = os.path.join(
                albumPath, f"{str(ep['index']).zfill(2)}. {epMeta['title']}.srt")
            self.downloadAndTag(epMeta, trackPath, srtPath, coverPath)


if __name__ == '__main__':
    print(TITLE)
    parser = argparse.ArgumentParser(
        prog='kuku-dl',
        description='KuKu FM Downloader!',
    )
    parser.add_argument('url', help="Show Url")
    args = parser.parse_args()
    KuKu(args.url).downAlbum()
