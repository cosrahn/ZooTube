#!/usr/bin/env python3

import shutil
import time
import argparse
import redis

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('T', type=str)
parser.add_argument('C', type=str)
parser.add_argument('Y', type=int)
parser.add_argument('m', type=int)
parser.add_argument('d', type=int)
parser.add_argument('H', type=int)
parser.add_argument('M', type=int)
parser.add_argument('S', type=int)

args = parser.parse_args()

last = ""
event_counter = 0

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
if args.T == "start":
    date_str = f"{args.Y:04d}-{args.m:02d}-{args.d:02d} {args.H:02d}:{args.M:02d}:{args.S:02d}"
    r.set("last", date_str)

    event_counter = r.get("event_counter")
    key = f'event:{args.C}:{event_counter}'
    r.hset(key, mapping={
        'camera_id': args.C,
        'start': date_str,
    })
    r.expire(key, 86400)
    with open("/tmp/on_event.log", "a") as f:
        f.write(f"{time.time()} {args.C} event {args.T} date {args.Y:04d}-{args.m:02d}-{args.d:02d} {args.H:02d}:{args.M:02d}:{args.S:02d}\n")

elif args.T == "stop":
    last = r.get("last")

    date_str = f"{args.Y:04d}-{args.m:02d}-{args.d:02d} {args.H:02d}:{args.M:02d}:{args.S:02d}"
    event_counter = r.incr("event_counter")
    key = f'event:{args.C}:{event_counter-1}'
    r.hset(key, mapping={
        'stop': date_str,
    })
    r.expire(key, 86400)
    x = r.hgetall(key)

    with open("/tmp/on_event.log", "a") as f:
        f.write(f"{time.time()} {args.C} event {args.T} date {args.Y:04d}-{args.m:02d}-{args.d:02d} {args.H:02d}:{args.M:02d}:{args.S:02d} last event {last} {x} \n")

    r.publish("chicken_army_camp", key)
