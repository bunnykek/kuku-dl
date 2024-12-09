# kuku-dl
Kuku FM downloader!

### Features
- Downloads podcasts/story/etc.
- Tags the tracks/eps with all the necessary metadata and cover artwork.
- Subtitles

### Installation Instructions

#### Windows
1. Install Python (3.7 or higher)
   ```bash
   # Download Python from https://www.python.org/downloads/
   # During installation, make sure to check "Add Python to PATH"
   ```

2. Install FFmpeg
   ```bash
   # Method 1: Using winget (Windows Package Manager)
   winget install FFmpeg

   # Method 2: Manual Installation
   # 1. Download FFmpeg from https://www.gyan.dev/ffmpeg/builds/
   # 2. Extract the zip file
   # 3. Add the bin folder to System PATH
   ```

3. Install Python dependencies
   ```bash
   pip install -r requirements.txt
   ```

#### MacOS
1. Install Homebrew (if not already installed)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install Python and FFmpeg
   ```bash
   brew install python3
   brew install ffmpeg
   ```

3. Install Python dependencies
   ```bash
   pip3 install -r requirements.txt
   ```

#### Linux (Ubuntu/Debian)
1. Update package list and install Python, pip, and FFmpeg
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip ffmpeg
   ```

2. Install Python dependencies
   ```bash
   pip3 install -r requirements.txt
   ```

#### Linux (Fedora)
1. Install Python, pip, and FFmpeg
   ```bash
   sudo dnf install python3 python3-pip ffmpeg
   ```

2. Install Python dependencies
   ```bash
   pip3 install -r requirements.txt
   ```

### Usage     
```bash
# Windows
python kuku.py [url]

# MacOS/Linux
python3 kuku.py [url]
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
