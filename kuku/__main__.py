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

import argparse

from .dl import KuKu, asyncio

BANNER = """\033[32m
oooo    oooo             oooo    oooo                     oooooooooo.   ooooo                 oooooooooooo 
`888   .8P'              `888   .8P'                      `888'   `Y8b  `888'                d'""""""d888' 
 888  d8'    oooo  oooo   888  d8'    oooo  oooo           888      888  888                       .888P   
 88888[      `888  `888   88888[      `888  `888           888      888  888                      d888'    
 888`88b.     888   888   888`88b.     888   888  8888888  888      888  888         8888888    .888P      
 888  `88b.   888   888   888  `88b.   888   888           888     d88'  888       o           d888'    .P 
o888o  o888o  `V88V"V8P' o888o  o888o  `V88V"V8P'         o888bood8P'   o888ooooood8         .8888888888P  
                                                                                                           
                                            By @bunnykek
                                            Modded By @kaif-00z                                                                                                    
\033[0m"""

if __name__ == "__main__":
    print(BANNER)
    parser = argparse.ArgumentParser(prog="kuku-dl", description="KuKu FM Downloader!")

    parser.add_argument("url", type=str, help="The URL of the podcast or album to download")
    parser.add_argument(
    "--path",
    type=str,
    default="downloads",
    help="Directory to save the album (default: 'downloads')."
)
    parser.add_argument(
        "--rip-subtitles",
        action="store_true",
        default=False,
        help="Enable this option to extract subtitles (default: False)."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of batches to divide task. (default: 5)."
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        default=False,
        help="Enable this option to create a ZIP archive of the downloaded files (default: False)."
    )
    parser.add_argument(
        "--episode",
        type=int,
        default=0,
        help="Specify the episode number to download (default: 0 for all episodes)."
    )
    parser.add_argument(
        "--season",
        type=int,
        default=1,
        help="Specify the season number the episode belongs to (default: 1)."
    )

    args = parser.parse_args()
    KUKU = KuKu(args.url, args.path, args.rip_subtitles, args.batch_size, args.archive)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop =  asyncio.get_event_loop_policy().get_event_loop()

    if args.episode:
        loop.run_until_complete(KUKU.downloadEpisode(args.episode, args.season))
    else:
        loop.run_until_complete(KUKU.downloadAlbum())
