import requests
import subprocess
import os
import re
from urllib.parse import urlparse
from mutagen.mp4 import MP4, MP4Cover

class KuKu:
    def __init__(self) -> None:
        """
        __init__()

        initializes a session to be used to recieve API data from KukuFM.
        """
        self.params = {
        'lang': 'english',
        'page': '1',
        }
        value, key = ('jwtToken', "Enter JWT here")
        if key == "Enter JWT here":
            raise ValueError("Invalid Token")
        self.session = requests.Session()
        self.session.cookies.set(value, key)
        
    def get(self, storyID: str, page=1) -> dict:
        """
        get()

        Method to send a requests over to KukuFM servers in order to recieve metadata, and HLS stream.

        @param storyID: Str value of the story ID used to identifiy books over to KukuFM API
        @param page: Str value to index which page used for KukuFM API.
        """
        self.params['page'] = page
        response = self.session.get(
                url = (f'https://kukufm.com/api/v2.1/channels/%s/episodes/' % storyID),
                params = self.params
            )
        if not response:
            raise ValueError("Unable to get response")
        
        return response.json()

    def getMetadata(self, storyID: str) -> dict:
        """
        getMetadata()

        Method to parse metadata from KukuFM API into a dict format.

        @param storyID: Str value of the story ID used to identifiy books over to KukuFM API
        """
        meta = self.get(storyID).get("show")
        metadata = {}
        metadata['title'] = meta['title'].strip()
        metadata['image'] = meta['original_image'].strip()
        metadata['date'] = meta['published_on'].strip()
        metadata['fictional'] = str(meta['is_fictional'])
        metadata['nEpisodes'] = meta['n_episodes']
        metadata['author'] = meta['author']['name'].strip()
        metadata['lang'] = meta['language'].capitalize().strip()
        metadata['type'] = meta['content_type']['title'].strip()
        metadata['ageRating'] = meta['meta_data']['age_rating'].strip()

        metadata['credits'] = {}
        # TODO Redo the way this is handled properly in order to save a list of names properly to the metadata.
        for credit in meta['credits'].keys():
            tempList = []
            for person in meta['credits'][credit]:
                tempList.append(person['full_name'])
            metadata['credits'][credit] = ', '.join(tempList)

        return metadata

    def sanitiseName(self, name) -> str:
        return re.sub(r'[:]', ' - ', re.sub(r'[\\/*?"<>|$]', '', re.sub(r'[ \t]+$', '', str(name).rstrip())))

    def downloadAndTag(self, episodeMetadata: dict, storyMetadata: dict, path: str, coverPath: str) -> None:
        """
        downloadAndTag()

        Method to download and tag locally using the KukuFM API and FFMPEG

        @param episodeMetadata: dict object that includes the track metadata.
        @param storyMetadata: dict object that includes the story metadata.
        @param path: str which sets a path to be downloaded to.
        @param coverPath: str path which locates where cover art is, so it'll be embeded within the file.
        """
        print('Downloading', episodeMetadata['title'], flush=True)
        if os.path.exists(path):
            print(episodeMetadata['title'], 'already exists!', flush=True)
            return
        # TODO Redo the use of FFMPEG as it's useless. and is worse
        subprocess.Popen(['ffmpeg', '-i', episodeMetadata['hls'],
                         '-map', 'p:2', '-c', 'copy', '-y', '-hide_banner', '-loglevel', 'error', path]).wait()
        tag = MP4(path)
        tag['\xa9alb'] = [storyMetadata['title']]
        tag['\xa9ART'] = [storyMetadata['author']]
        tag['aART'] = [storyMetadata['author']]
        tag['\xa9day'] = [episodeMetadata['date'][0:10]]
        tag['trkn'] = [(int(episodeMetadata['epNo']), int(storyMetadata['nEpisodes']))]
        tag['stik'] = [2]
        tag['\xa9nam'] = [episodeMetadata['title']]
        tag.pop("©too")

        tag['----:com.apple.iTunes:Fictional'] = bytes(
            str(storyMetadata["fictional"]), 'UTF-8')
        tag['----:com.apple.iTunes:Author'] = bytes(str(storyMetadata["author"]), 'UTF-8')
        tag['----:com.apple.iTunes:Language'] = bytes(str(storyMetadata["lang"]), 'UTF-8')
        tag['----:com.apple.iTunes:Type'] = bytes(str(storyMetadata["type"]), 'UTF-8')
        tag['----:com.apple.iTunes:Season'] = bytes(str(episodeMetadata["seasonNo"]), 'UTF-8')
        tag['----:com.apple.iTunes:Age rating'] = bytes(
            str(storyMetadata["ageRating"]), 'UTF-8')

        for cat in storyMetadata['credits'].keys():
            credit = cat.replace('_', ' ').capitalize()
            tag[f'----:com.apple.iTunes:{credit}'] = bytes(
                str(storyMetadata['credits'][cat]), 'UTF-8')
        with open(coverPath, 'rb') as f:
            pic = MP4Cover(f.read())
            tag['covr'] = [pic]
        tag.save()


    def downAlbum(self, storyID) -> None:
        """
        downAlbum()

        Method where it'll prepare a storyID to be stored onto locally.

        @param storyID: Str value of the story ID used to identifiy books over to KukuFM API
        """
        albMetadata = self.getMetadata(storyID)
        folderName = f"{albMetadata['title']} "
        folderName +=  f"({albMetadata['date'][:4]}) " if albMetadata.get('date') else ''
        folderName +=  f"[{albMetadata['lang']}]"
        
        albumPath = os.path.join(
            os.getcwd(), 'Downloads', albMetadata['lang'], albMetadata['type'], self.sanitiseName(folderName))

        if not os.path.exists(albumPath):
            os.makedirs(albumPath)

        with open(os.path.join(albumPath, 'cover.png'), 'wb') as f:
            f.write(self.session.get(albMetadata['image']).content)

        for i in range(1, 20000):
            response = self.get(storyID = storyID, page = i)
            for ep in response['episodes']:
                print(ep['title'].strip())
                epMeta = {}
                epMeta['title'] = re.sub(r"\d+.", "", ep['title']).strip()
                epMeta['hls'] = ep['content']['hls_url'].strip()
                epMeta['epNo'] = ep['index']
                epMeta['seasonNo'] = ep['season_no']
                epMeta['date'] = ep['published_on'].strip()
                trackPath = os.path.join(albumPath, f"{str(ep['index']).zfill(2)}. {epMeta['title']}.m4a")
                try:
                    self.downloadAndTag(epMeta, albMetadata, trackPath,
                                   os.path.join(albumPath, 'cover.png'))

                except Exception as e:
                    print(ep['title'], e, flush=True)
            if not response.get('has_more'):
                break

if __name__ == '__main__':
    kukuSession = KuKu()
    url = input("Enter kukufm URL: ")
    kukuURL = urlparse(url)
    kukuID = kukuURL.path.split('/')[-1]

    kukuSession.downAlbum(kukuID)