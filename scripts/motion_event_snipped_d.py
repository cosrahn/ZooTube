#!/usr/bin/env python3

"""
This script is used to create a clip from a motion event.
"""

import time
import redis
from datetime import datetime
from os import listdir, mkdir, remove
from os.path import isfile, join, getmtime, split
import shutil
from string import Template
import subprocess
import json
import pytz

mypath = "/var/www/html/streaming/"
vodpath = "/var/www/html/vod"

r = redis.Redis(
    host='127.0.0.1',
    port=6379,
    decode_responses=True
)

mobile = r.pubsub()

mobile.subscribe("chicken_army_camp")

for message in mobile.listen():
    # {'type': 'message', 'pattern': None, 'channel': 'chicken_army_camp', 'data': 'event:0:13'}
    print(message)
    if message["type"] == "message":
        event_data = r.hgetall(message["data"])
        print(event_data)
        tz = pytz.timezone('Europe/Berlin')
        start_datetime_object = datetime.strptime(
            event_data["start"], '%Y-%m-%d %H:%M:%S')  # .replace(tzinfo=tz)
        stop_datetime_object = datetime.strptime(
            event_data["stop"], '%Y-%m-%d %H:%M:%S')  # .replace(tzinfo=tz)

        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        m4s_files = [f for f in onlyfiles if f.endswith('.m4s')]

        m4s_time_files = [f for f in m4s_files if isfile(f"{mypath}/{f}") and getmtime(
            f"{mypath}/{f}") >= start_datetime_object.timestamp() and getmtime(f"{mypath}/{f}") <= stop_datetime_object.timestamp()]
        # print(m4s_time_files)
        if len(m4s_time_files) <= 0:
            print("Empty file list")
            continue
        print(f"processing file list {len(m4s_time_files)}")

        vod_part_ts = int(start_datetime_object.timestamp())
        st_vodpath = f"{vodpath}/{vod_part_ts}"

        mkdir(st_vodpath)
        mkdir(f"{st_vodpath}/data")
        ffmpeg_filelist_s0 = list()
        ffmpeg_filelist_s1 = list()
        shutil.copyfile(f"{mypath}/init-stream0.m4s",
                        f"{st_vodpath}/data/init-stream0.m4s")
        shutil.copyfile(f"{mypath}/init-stream1.m4s",
                        f"{st_vodpath}/data/init-stream1.m4s")
        for filename in m4s_time_files:
            shutil.copyfile(f"{mypath}/{filename}",
                            f"{st_vodpath}/data/{filename}")
            if "chunk-stream1" in filename:
                ffmpeg_filelist_s1.append(filename)
            else:
                ffmpeg_filelist_s0.append(filename)

        print(f"found HighRes files {len(ffmpeg_filelist_s0)}")
        print(f"found LowRes files {len(ffmpeg_filelist_s1)}")

        if len(ffmpeg_filelist_s0) <= 0:
            print(f"no files in HighRes, use LowRes files")
            with open(f"{st_vodpath}/media_0.m4s", "wb") as f:
                with open(f"{st_vodpath}/data/init-stream1.m4s", mode="rb") as init_stream:
                    f.write(init_stream.read())
                for fname in reversed(ffmpeg_filelist_s1):
                    with open(f"{st_vodpath}/data/{fname}", mode="rb") as chunk_stream:
                        f.write(chunk_stream.read())
        else:
            print(f"combine HighRes files")
            with open(f"{st_vodpath}/media_0.m4s", "wb") as f:
                with open(f"{st_vodpath}/data/init-stream0.m4s", mode="rb") as init_stream:
                    f.write(init_stream.read())
                for fname in reversed(ffmpeg_filelist_s0):
                    with open(f"{st_vodpath}/data/{fname}", mode="rb") as chunk_stream:
                        f.write(chunk_stream.read())

        print(f"combine LowRes files")
        with open(f"{st_vodpath}/media_1.m4s", "wb") as f:
            with open(f"{st_vodpath}/data/init-stream1.m4s", mode="rb") as init_stream:
                f.write(init_stream.read())
            for fname in reversed(ffmpeg_filelist_s1):
                with open(f"{st_vodpath}/data/{fname}", mode="rb") as chunk_stream:
                    f.write(chunk_stream.read())

        print(f"remove HighRes chunks")
        for fname in reversed(ffmpeg_filelist_s0):
            remove(f"{st_vodpath}/data/{fname}")
        print(f"remove LowRes chunks")
        for fname in reversed(ffmpeg_filelist_s1):
            remove(f"{st_vodpath}/data/{fname}")

        print(f"run ffmpeg to create dash VOD and Download files")
        # ffmpeg -i media_0.m4s -i media_1.m4s -c:v copy -map 0:v -map 1:v -f dash -seg_duration 2 -use_timeline 1 -window_size 3600 -hls_playlist 1 -adaptation_sets "id=0,streams=v id=1,streams=a" manifest.mpd
        chunk_command = ['/usr/bin/ffmpeg', '-y', '-loglevel', 'error', '-i', f'{st_vodpath}/media_0.m4s', '-i', f'{st_vodpath}/media_1.m4s', '-c:v', 'copy', '-map', '0:v', '-map', '1:v',
                         '-f', 'dash', '-seg_duration', '2', '-use_timeline', '1', '-window_size', '3600', '-hls_playlist', '1', '-adaptation_sets', '"id=0,streams=v id=1,streams=a"', f'{st_vodpath}/manifest.mpd']
        download_ts_high_command = ['/usr/bin/ffmpeg', '-y', '-loglevel', 'error', '-i',
                                    f'{st_vodpath}/media_0.m4s', '-c:v', 'copy', '-an', '-f', 'mpegts', f'{st_vodpath}/ChickenRun_{vod_part_ts}_HighRes.ts']
        download_ts_low_command = ['/usr/bin/ffmpeg', '-y', '-loglevel', 'error', '-i',
                                   f'{st_vodpath}/media_1.m4s', '-c:v', 'copy', '-an', '-f', 'mpegts', f'{st_vodpath}/ChickenRun_{vod_part_ts}_LowRes.ts']
        with open(f"{st_vodpath}/ffmpeg_line.sh", "w") as ffmpeg:
            ffmpeg.write("#!/bin/bash\n")
            ffmpeg.write(f"cd {st_vodpath}\n")
            ffmpeg.write(" ".join(chunk_command))
            ffmpeg.write("\n")
            ffmpeg.write(" ".join(download_ts_high_command))
            ffmpeg.write("\n")
            ffmpeg.write(" ".join(download_ts_low_command))
            ffmpeg.write("\n")
        chunk_command = ["/bin/bash", f"{st_vodpath}/ffmpeg_line.sh"]
        subprocess.call(chunk_command)

        print(f"remove old media_*,m4s")
        remove(f'{st_vodpath}/media_0.m4s')
        remove(f'{st_vodpath}/media_1.m4s')
        remove(f"{st_vodpath}/ffmpeg_line.sh")

        print(f"create video_list.json")
        vodfiles = [[f"{datetime.fromtimestamp(int(f) + 3600)}", f"/vod/{f}/manifest.mpd", "", f"{int(f)}"]
                    for f in listdir(vodpath) if not isfile(join(vodpath, f))]
        vodfiles.sort()

        vod_comment_dict = dict()
        counter = 0
        for vod_ts, vodfile, vod_comment, vod_timestamp in vodfiles:
            vod_path, _ = split(vodfile)
            if isfile(f"/var/www/html/{vod_path}/comment.txt"):
                with open(f"/var/www/html/{vod_path}/comment.txt", "r") as vod_comment_f:
                    vod_comment_dict[counter] = vod_comment_f.read()
            counter += 1

        for k, v in vod_comment_dict.items():
            vodfiles[k][2] = v

        with open(f"{vodpath}/video_list.json", "w") as jsonf:
            jsonf.write(json.dumps(list(reversed(vodfiles))))

        print("done")
