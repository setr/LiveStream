# LiveStream
Host a live stream of a video for shared syncronized viewing, for 1 cent an hour, through digital ocean

## Requirements
Requires an account with digital ocean, and an [API KEY](https://www.digitalocean.com/community/tutorials/how-to-use-the-digitalocean-api-v2)

Requires python2.7

Requires ffmpeg if you want the script to stream for you (The `play` command). Otherwise, programs such as [VLC](https://www.videolan.org/vlc/index.html) or [OBS](https://obsproject.com/) can be used instead to generate an RTMP stream (use commands `start_server` and `destroy_server` to deploy the server, and point the RTMP stream at the provided url).

If subs are needed, then ffmpeg must be compiled with libass for subtitle conversion. Not necessary if you don't want subs.

View the stream with any player that supports RTMP. [VLC](https://www.videolan.org/vlc/index.html) or [MPV](https://mpv.io/) are suggested. Requires **flash** to view the stream. 

Only tested on OSX. Should work on any Linux box with no issues. 

### Windows

Windows is untested, but `start_server` and `destroy_server` subcommands **should** work with no issues. The `play` subcommand may not. 

If it doesn't, run start_server to deploy the server, then use VLC or OBS to create an RTMP stream pointed at the provided url. Just make sure to call destroy_server when you're done.

Only tested on OSX. Should work on Linux with no issues. Might work on Windows (particularly the ffmpeg call might break). OBS/VLC would probably be more convenient for Windows users.

## Install
OSX (brew) install:
```sh
brew install ffmpeg --with-libass # this will take like 30 min
pip install click requests
git clone https://github.com/setr/LiveStream.git

cd LiveStream
python spawn.py --help
```

## Usage
```
Usage: spawn.py [OPTIONS] FILENAMEh

Options:
  --api-key TEXT   Digital Ocean API key; if not provided on CLI, it must be
                   provided in the file API_KEY
  --subs           Whether or not subtitles are encoded in the movie. If they
                   are, they'll be burned into the stream
  --snapshot TEXT  Name of snapshot image to use instead of creating a brand
                   new VM [ NOT IMPLEMENTED ]
  --help           Show this message and exit.
```

Examples:

Start the Server, stream the movie, stop the server
```
$ python spawn.py play --subs ~/Downloads/KungFu/Police-Story-3-720p.mkv

test% python spawn.py play --subs ~/Downloads/KungFu/Legend-of-the-Drunken-Master_720p.mkv
Attempt #1/3: Starting up the VM...
VM at ip 45.55.141.12 is now active
Attempt #1/20: Waiting for nginx to finish compiling...
Attempt #2/20: Waiting for nginx to finish compiling...
Attempt #3/20: Waiting for nginx to finish compiling...
Attempt #4/20: Waiting for nginx to finish compiling...
Attempt #5/20: Waiting for nginx to finish compiling...
Attempt #6/20: Waiting for nginx to finish compiling...
Attempt #7/20: Waiting for nginx to finish compiling...
Attempt #8/20: Waiting for nginx to finish compiling...
Attempt #9/20: Waiting for nginx to finish compiling...

Running command: ffmpeg -re -loglevel warning -i /Users/setr/Downloads/KungFu/Legend-of-the-Drunken-Master_720p.mkv -c:v libx264 -c:a libmp3lame -filter:v subtitles=/Users/setr/Downloads/KungFu/Legend-of-the-Drunken-Master_720p.mkv -ar 44100 -ac 1 -f flv rtmp://45.55.141.12/live

The stream is now live at rtmp://45.55.141.12/live
Enjoy!
```

Start the server and set it up for streaming, but don't stream anything
```
$ python spawn.py start_server

Starting server
VM at ip 104.236.192.177 is now active
Attempt #7/20: Waiting for nginx to finish compiling...
Server is ready! Point an RTMP stream at rtmp://104.236.192.177/live
```

Destroy any running servers created by this script
```
$ python spawn.py destroy_server

Attempt #1/3: Trying to kill VM with tag f48dff2e-7fb7-49e8-b9bf-2013c9deff90...
```

## Important Notes
* If something goes wrong, make sure to go to digitalocean.com and destroy the VM yourself (named StreamServer), or call the `destroy_server` command. The script **does not** ensure multiple servers are not created. Each server will cost you $5/monthly if you never close them.
* ffmpeg will be converting and streaming the video at the same time, in real time. If your computer converts slower than the bitrate of the video, you'll end up with a choppy stream. Consider converting the video beforehand in this case.
* This uses the RTMP protocol, which communicates with Adobe Flash. Thus, you'll need flash installed to view the stream. 
* The server is not secure in any fashion and makes no check as to **who** is streaming the video to the server. It also doesn't stop other people from streaming videos through your server. Such malicious users won't really cost you anything, except eating up some of your bandwidth cap.

## What it does

1. Starts up a new Digital Ocean VM on the lowest tier (512MB), and runs deploy.sh 
  * deploy.sh downloads Nginx and the RTMP module, and compiles it on the VM
  * Nginx is used to run an rtmp server, on port 1935 (rtmp default)
2. Once Nginx is running, the local machine uses ffmpeg to stream the video to rtmp://`ip`/live
  * ffmpeg converts the video to h264, audio to mp3 and burns the subtitles into the output, wrapped in an flv container
  * ffmpeg will be converting and streaming the video at the same time, in real time. If your computer converts slower than the bitrate of the video, you'll end up with a choppy stream. Consider converting the video beforehand in this case.
3. The video can then be viewed from the same url rtmp://`ip`/live
4. When the video finishes, the script will destroy the VM.

This means that you have one input stream, from the local computer to the digital ocean vm, and `n` output streams for `n` viewers. 

The command `play` will execute all of the above. `start_server` will only execute step 1, and `destroy_server` will only execute step 4. 


## Calculations
### Total Network Traffic
Digital Ocean allows 1 TB of network traffic per month. The traffic of playing a single video:

s = size of the video after conversion to flv

n = number of viewers

Total Bandwidth used = (n + 1) * s

The +1 is from your computer streaming to the server. 

In testing, a 1.5 GB h264 mkv video converted to 750 MB flv. So with 10 viewers, I had a total traffic of (n + 1) * 750MB = (10 + 1) * 750 = 8250 MB = ~8GB network traffic.

### Bandwidth Per Second
According to a [Digital Ocean Mod](https://www.digitalocean.com/community/questions/upload-and-download-speed-of-a-droplet), expected upload speed is 330 Mbps

n = number of viewers

max(n) = 330Mbps / video-bitrate

My converted test movie had a bitrate of 1278 kb/s (`ffprobe test.flv`). So 330Mbps * 1024 = 337920 kb/s / 1278 kb/s = ~264 max number of viewers. Real network conditions will probably allow much less than that, and some claim Digital Ocean provides significantly lower upload speeds, so real usage may vary.

### Cost per video
[Digital Ocean](https://www.digitalocean.com/pricing/#droplet) charges $0.007 per hour of server uptime. 

The cost of a 2 hour movie is 2 * $0.007 = $0.014

The cost of a weekly 2 hour movie is 4 * $0.014 = $0.056

When charged at the end of the month, it'll be rounded up, so $0.06, or 6 cents.

### Bi-Weekly Movie, 30 viewers, 2 GB movie, 1300 kb/s bitrate

Total Bandwidth Per Session = (n + 1) * s = 31 * 2GB = 62 GB

Total Bandwidth Per Month = 62GB * 8 Sessions = 496 GB

Upload Speed Required Per Session = (n + 1) users * bitrate = 31 * 1300kb/s = 40,300 kb/s = ~39 Mb/s

Total cost = 2 hr/movie * 0.007 $/hr * 8 Sessions = $0.112 = $0.11 per month

## Why Digital Ocean
[AWS](https://aws.amazon.com/free/faqs/) only allows 15GB total network traffic per month on its free tier. Otherwise, its $0.09 per GB.

[GCP](https://cloud.google.com/free/docs/always-free-usage-limits) only allows 1 GB outgoing traffic per day (~30GB/mo) on its free tier. Otherwise, $0.09 per GB

[Microsoft Azure](https://azure.microsoft.com/en-us/pricing/details/bandwidth/?cdn=disable) allows 5GB free per month. Otherwise $0.09 per GB

[Linode](https://www.linode.com/pricing) requires an up-front payment of min. $5 to use their service. Otherwise, pricing is comparable to Digital Ocean ($.0075/hr for the cheapest server, 1TB transfer, 1 Gbps upload).

[Digital Ocean](https://www.digitalocean.com/pricing/#droplet) has no up-front cost, and $.007/hr pricing, 1 TB transfer, 330 Mbps upload.

## Future
Provide instructions for streaming through [VLC](https://www.videolan.org/vlc/index.html) and [OBS](https://obsproject.com/)

Optionally start up an HLS/Dash feed instead (or alongside?) RTMP, and I guess a webpage to go with it.

FFMPEG can apparently take a url as input, so we might as well support that too (currently blocked because the script checks if video is a valid file)

Only accept streams from ip address that ran this script, or from a list of given IP's.

Maybe maintain a pre-compiled version of Nginx in this repo, to speed up deployment. 

Make the script installable.

Add proper logging and loglevels
