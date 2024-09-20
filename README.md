# kuku-dl
Kuku FM downloader!

### Features
- Downloads podcasts/story/etc.
- Tags the tracks/eps with all the necessary metadata and cover artwork.
- Subtitles

### You can use docker container or install the package locally : 

#### Docker container
- build docker image : ``docker build . -t kuku-dl``
- run docker image : ``docker run -v ./Downloads:/kuku-dl/Downloads kuku-dl [KUKUFM_URL]``

#### Install locally
- Install [FFMPEG](https://ffmpeg.org/)
- `pip install requirements.txt`

### Usage     
      
```
python kuku.py [url]
```

### Sample MediaInfo
```
General
Complete name                            : Downloads\Hindi\Audio Book\Swami Vivekanand (2019) [Hindi]\001. 1.  Swami Vivekanand.m4a
Format                                   : MPEG-4
Format profile                           : Apple audio with iTunes info
Codec ID                                 : M4A  (M4A /isom/iso2)
File size                                : 2.36 MiB
Duration                                 : 3 min 47 s
Overall bit rate mode                    : Constant
Overall bit rate                         : 86.9 kb/s
Season                                   : 1
Album                                    : Swami Vivekanand
Album/Performer                          : Raj Shrivastava
Track name                               : 1.  Swami Vivekanand
Track name/Position                      : 1
Track name/Total                         : 64
Performer                                : Raj Shrivastava
ContentType                              : Audiobook
Recorded date                            : 2019-07-30
Cover                                    : Yes
Age rating                               : 13+
Fictional                                : False
Language                                 : Hindi
Type                                     : Audio Book
Author                                   : Raj Shrivastava
Voice artists                            : Raj Shrivastava

Audio
ID                                       : 1
Format                                   : AAC LC SBR
Format/Info                              : Advanced Audio Codec Low Complexity with Spectral Band Replication
Commercial name                          : HE-AAC
Format settings                          : Implicit
Codec ID                                 : mp4a-40-2
Duration                                 : 3 min 47 s
Bit rate mode                            : Constant
Bit rate                                 : 62.8 kb/s
Channel(s)                               : 2 channels
Channel layout                           : L R
Sampling rate                            : 44.1 kHz
Frame rate                               : 21.533 FPS (2048 SPF)
Compression mode                         : Lossy
Stream size                              : 1.70 MiB (72%)
Default                                  : Yes
Alternate group                          : 1
```
### Disclaimer
- I will not be responsible for how you use kuku-dl.    
