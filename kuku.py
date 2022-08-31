import requests
import subprocess
import os
from mutagen.mp4 import MP4, MP4Cover

session = requests.Session()
cookies = {
    'jwtToken': 'get_the_jwtToken_value_from_browser_cookies',
}

params = {
    'lang': 'english',
    'page': '1',
}


def getMetadata(aid):
    params['page'] = '1'
    response = session.get(
        f'https://kukufm.com/api/v2.1/channels/{aid}/episodes/', params=params, cookies=cookies)
    meta = response.json()['show']
    metadata = {}
    metadata['title'] = meta['title'].strip()
    metadata['image'] = meta['original_image'].strip()
    metadata['date'] = meta['published_on'].strip()
    metadata['fictional'] = 'True' if meta['is_fictional'] else 'False'
    metadata['nEpisodes'] = meta['n_episodes']
    metadata['author'] = meta['author']['name'].strip()
    metadata['lang'] = meta['language'].capitalize().strip()
    metadata['type'] = meta['content_type']['title'].strip()
    metadata['ageRating'] = meta['meta_data']['age_rating'].strip()

    metadata['credits'] = {}

    for credit in meta['credits'].keys():
        tempList = []
        for person in meta['credits'][credit]:
            tempList.append(person['full_name'])
        metadata['credits'][credit] = ', '.join(tempList)

    return metadata


def downloadandTag(ep, album, path, coverPath):
    print('Downloading', ep['title'], flush=True)
    if os.path.exists(path):
        print(ep['title'], 'already exists!', flush=True)
        return
    subprocess.Popen(['ffmpeg', '-i', ep['hls'],
                     '-c', 'copy', '-y', '-hide_banner', '-loglevel', 'error', path]).wait()
    tag = MP4(path)
    tag['\xa9alb'] = [album['title']]
    tag['\xa9ART'] = [album['author']]
    tag['aART'] = [album['author']]
    tag['\xa9day'] = [ep['date'][0:10]]
    tag['trkn'] = [(int(ep['epNo']), int(album['nEpisodes']))]
    tag['stik'] = [2]
    tag['\xa9nam'] = [ep['title']]
    tag.pop("©too")

    tag['----:com.apple.iTunes:Fictional'] = bytes(
        str(album["fictional"]), 'UTF-8')
    tag['----:com.apple.iTunes:Author'] = bytes(str(album["author"]), 'UTF-8')
    tag['----:com.apple.iTunes:Language'] = bytes(str(album["lang"]), 'UTF-8')
    tag['----:com.apple.iTunes:Type'] = bytes(str(album["type"]), 'UTF-8')
    tag['----:com.apple.iTunes:Season'] = bytes(str(ep["seasonNo"]), 'UTF-8')
    tag['----:com.apple.iTunes:Age rating'] = bytes(
        str(album["ageRating"]), 'UTF-8')

    for cat in album['credits'].keys():
        credit = cat.replace('_', ' ').capitalize()
        tag[f'----:com.apple.iTunes:{credit}'] = bytes(
            str(album['credits'][cat]), 'UTF-8')
    with open(coverPath, 'rb') as f:
        pic = MP4Cover(f.read())
        tag['covr'] = [pic]
    tag.save()


def downAlbum(aid):
    albMetadata = getMetadata(aid)
    folderName = f"{albMetadata['title']} ({albMetadata['date'][:4]}) [{albMetadata['lang']}]"
    print(folderName, flush=True)
    albumPath = os.path.join(
        os.getcwd(), 'Downloads', albMetadata['lang'], albMetadata['type'], folderName)

    if not os.path.exists(albumPath):
        os.makedirs(albumPath)

    with open(os.path.join(albumPath, 'cover.png'), 'wb') as f:
        f.write(session.get(albMetadata['image']).content)

    for i in range(1, 20000):
        params['page'] = str(i)
        response = session.get(
            f'https://kukufm.com/api/v2.1/channels/{aid}/episodes/', params=params, cookies=cookies)
        for ep in response.json()['episodes']:
            epMeta = {}
            epMeta['title'] = ep['title'].strip()
            epMeta['hls'] = ep['content']['hls_url'].strip()
            epMeta['epNo'] = ep['index']
            epMeta['seasonNo'] = ep['season_no']
            epMeta['date'] = ep['published_on'].strip()
            trackPath = os.path.join(albumPath, str(
                ep['index']).zfill(3)+'. '+ep['title']+'.m4a')
            try:
                downloadandTag(epMeta, albMetadata, trackPath,
                               os.path.join(albumPath, 'cover.png'))

            except Exception as e:
                print(ep['title'], e, flush=True)
        if not response.json()['has_more']:
            break

if __name__ == '__main__':
    if cookies['jwtToken'] is 'get_the_jwtToken_value_from_browser_cookies':
        print("Please update the cookie in line number 8!")
        exit(1)
    url = input("Enter kukufm URL:")
    id = url.split('/')[-1]
    downAlbum(id)