# ZooTube
A website to manage video files of your home zoo like chickens or ducks.

## Setup

Use a Raspberry Pi with [mediamtx](https://github.com/bluenviron/mediamtx) or a ONVIF capable camera.

Start a ffmpeg to adapt rtsp to web.
```console
ffmpeg -loglevel warning -thread_queue_size 4096 -fflags +genpts -r 25  -rtsp_transport tcp -i rtsp://192.168.1.95:8554/zootube_hd -thread_queue_size 4096 -fflags +genpts -r 25 -rtsp_transport tcp -i rtsp://192.168.1.95:8554/zootube_sd -c:v copy -map 0:v -map 1:v -f dash -seg_duration 2 -use_timeline 1 -window_size 1800 -remove_at_exit 1 -hls_playlist 1 -adaptation_sets "id=0,streams=v id=1,streams=a" /dev/shm/streaming/manifest.mpd
```

## FAQ

Q: Where is controlbar.js?
A: controlbar is a part of dash.js and you find it in submodule dash in path contrib/akamai/controlbar
