// Add your DASH video URLs here
var videoUrls = [
    ['Live', 'streaming/manifest.mpd'],
];
var quote = { "quote": 0 };
var last_clip_element = null;

var LiveVideo = document.getElementById('live');
var link = document.createElement('a');
link.href = 'javascript:void(0)';
//link.textContent = "LIVE";
link.innerHTML = "LIVE";
link.style.fontSize = "2em";
link.addEventListener('click', function () {
    changeToLiveSource('/streaming/manifest.mpd', 'Live Stream');
});
LiveVideo.appendChild(link);

var intervalId_01 = setInterval(function () {
    fetch('/vod/video_list.json', { cache: "no-cache" })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }
            return response.json();
        })
        .then(json => update_videoUrls(json))
        .catch(err => console.error(`Fetch problem: ${err.message}`));
}, 10000);

var intervalId_02 = setInterval(function () {
    fetch('/streaming/quote.json', { cache: "no-cache" })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }
            return response.json();
        })
        .then(json => update_quote(json))
        .catch(err => console.error(`Fetch problem: ${err.message}`));
}, 1000);

fetch('/vod/video_list.json', { cache: "no-cache" })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        return response.json();
    })
    .then(json => update_videoUrls(json))
    .catch(err => console.error(`Fetch problem: ${err.message}`));

function update_videoUrls(json_data) {
    videoUrls = json_data;
    UpdateVideoList();
}

function update_quote(json_data) {
    quote = json_data;

    var quote_element = document.getElementById('quote');
    while (quote_element.firstChild) {
        quote_element.removeChild(quote_element.firstChild);
    }
    quote_element.innerHTML = 'Zuschauer: ' + quote['quote'];
}

// Update the video source when a video is clicked in the list
function changeToLiveSource(sourceUrl, comment) {
    var video = document.querySelector("#videoPlayer");
    player.initialize(video, sourceUrl, true);

    UpdateComment(comment);

    var Download = document.getElementById('Download');
    while (Download.firstChild) {
        Download.removeChild(Download.firstChild);
    }
}

function changeVideoSource(vod_ts, comment) {
    sourceUrl = "/vod/" + vod_ts + '/manifest.mpd';

    var video = document.querySelector("#videoPlayer");
    player.initialize(video, sourceUrl, true);

    UpdateComment(comment);

    var Download = document.getElementById('Download');

    while (Download.firstChild) {
        Download.removeChild(Download.firstChild);
    }

    var link = document.createElement('a');
    link.href = "/vod/" + vod_ts + "/" + 'ChickenRun_' + vod_ts + '_HighRes.ts';
    link.textContent = "Download HighRes";
    Download.appendChild(link);

    var text = document.createTextNode(" | ");
    Download.appendChild(text);

    var Download = document.getElementById('Download');
    var link = document.createElement('a');
    link.href = "/vod/" + vod_ts + "/" + 'ChickenRun_' + vod_ts + '_LowRes.ts';
    link.textContent = "Download LowRes";
    Download.appendChild(link);
}

// Create the video list dynamically
function createVideoList() {
    var videoList = document.getElementById('video-list');
    videoUrls.forEach(function (url) {
        var listItem = document.createElement('li');
        var link = document.createElement('a');
        link.href = 'javascript:void(0)';
        if (url[2] === "") {
            link.textContent = url[0];
        } else {
            link.innerHTML = url[0] + ' &#11088;';
        }
        link.addEventListener('click', function () {
            changeVideoSource(url[3], url[2]);
        });
        listItem.appendChild(link);
        videoList.appendChild(listItem);
    });
}

// Update the video list dynamically
function UpdateVideoList() {
    var videoList = document.getElementById('video-list');
    while (videoList.firstChild) {
        videoList.removeChild(videoList.firstChild);
    }
    videoUrls.forEach(function (url) {
        var listItem = document.createElement('li');
        var link = document.createElement('a');
        link.href = 'javascript:void(0)';
        if (url[2] === "") {
            link.textContent = url[0];
        } else {
            link.innerHTML = url[0] + ' &#11088;';
        }
        // link.textContent = url[0];
        link.addEventListener('click', function () {
            changeVideoSource(url[3], url[2]);
        });
        listItem.appendChild(link);
        videoList.appendChild(listItem);
    });
}

function UpdateComment(comment) {
    var Comment_element = document.getElementById('Comment');

    while (Comment_element.firstChild) {
        Comment_element.removeChild(Comment_element.firstChild);
    }
    var comment_text = document.createTextNode(" " + comment + " ");
    Comment_element.appendChild(comment_text);
}

createVideoList();

var player = init();

function init() {
    var mpd_url = "/streaming/manifest.mpd"
    UpdateComment("Live stream");
    var video = document.querySelector("#videoPlayer");
    player = dashjs.MediaPlayer().create();
    player.on(dashjs.MediaPlayer.events.PLAYBACK_NOT_ALLOWED, function (data) {
        console.log('Playback did not start due to auto play restrictions. Muting audio and reloading');
        video.muted = true;
        player.initialize(video, mpd_url, true);
    });
    player.initialize(video, mpd_url, true);
    //        player.attachView(video);
    var controlbar = new ControlBar(player); //Player is instance of Dash.js MediaPlayer;
    controlbar.initialize();
    player.updateSettings({
        'streaming': {
            'lowLatencyEnabled': true,
            'liveDelay': 1,
            'liveCatchUpMinDrift': 0.05,
            'liveCatchUpPlaybackRate': 0.5
        }
    });
    return player;
}
