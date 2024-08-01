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

from .dl import Formats, KuKu, asyncio

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="kuku-dl", description="KuKu FM Downloader!")

    parser.add_argument("url", type=str, help="The URL of the video to download")
    parser.add_argument(
        "--format",
        choices=[Formats.HIGHEST, Formats.MEDIUM, Formats.LOWEST],
        default=Formats.LOWEST,
        help="The format to download the audio in (default: 128)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default="downloads",
        help="The path to save the Album (default: downloads)",
    )
    parser.add_argument(
        "--rip-subtitles",
        action="store_true",
        default=False,
        help="Whether to rip subtitles (default: False)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of Task In A Single Batch (default: 5)",
    )

    args = parser.parse_args()
    KUKU = KuKu(args.url, args.format, args.path, args.rip_subtitles, args.batch_size)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(KUKU.downloadAlbum())
