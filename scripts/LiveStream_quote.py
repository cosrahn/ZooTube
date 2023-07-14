#!/usr/bin/env python3

import os
import re
import time
import json
from typing import Iterator
import pytz
from datetime import datetime, timedelta

TIME_WINDOW = 5

lineformat = re.compile(
    r"""(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST) )(?P<url>.+)(http\/1\.1")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) (["](?P<refferer>(\-)|(.+))["]) (["](?P<useragent>.+)["])""", re.IGNORECASE)


def follow(file, sleep_sec=0.1) -> Iterator[str]:
    """ Yield each line from a file as they are written.
    `sleep_sec` is the time to sleep after empty reads. """
    sleep_sec = 0.1
    line = ''
    last_line_time = time.time()
    while True:
        tmp = file.readline()
#        if tmp is not None:
        if tmp is not "":
            line += tmp
            if line.endswith("\n"):
                last_line_time = time.time()
                yield line
                line = ''
        else:
            time.sleep(sleep_sec)
            if last_line_time + 60 < time.time():
                break


if __name__ == '__main__':
    while True:
        with open("/var/log/nginx/access.log", 'r') as file:
            try:  # catch OSError in case of a one line file
                file.seek(-2, os.SEEK_END)
                found_content = False
                while True:
                    c = f.read(1)
                    if not c.isspace():
                        found_content = True
                    if found_content and c == b'\n':
                        if found_content:
                            break
                    f.seek(-2, os.SEEK_CUR)
            except OSError:
                file.seek(0)
            unique_ip = dict()
            for line in follow(file):
                data = re.search(lineformat, line)
                if data:
                    datadict = data.groupdict()
                    ip = datadict["ipaddress"]
                    datetimestring = element = datetime.strptime(
                        datadict["dateandtime"], "%d/%b/%Y:%H:%M:%S %z")
                    url = datadict["url"]
                    bytessent = datadict["bytessent"]
                    referrer = datadict["refferer"]
                    useragent = datadict["useragent"]
                    status = datadict["statuscode"]
                    method = data.group(6)
                    if datetimestring.replace(tzinfo=None) > datetime.now() - timedelta(seconds=TIME_WINDOW):
                        if "/streaming/chunk-" in url:
                            unique_ip[ip] = datetimestring.replace(tzinfo=None)
                        for_delete = list()
                        for k, v in unique_ip.items():
                            if v < datetime.now() - timedelta(seconds=TIME_WINDOW):
                                for_delete.append(k)
                        for timeout_ip in for_delete:
                            del (unique_ip[timeout_ip])
#                        print(f"{len(unique_ip)} {ip} {datetimestring} {url} {useragent}")
                        quote = {
                            "quote": len(unique_ip),
                        }
                        # with open("/var/www/html/vod/quote.json", "w") as quote_fh:
                        with open("/dev/shm/streaming/quote.json", "w") as quote_fh:
                            quote_fh.write(json.dumps(quote))
        print("reload nginx access log file")
