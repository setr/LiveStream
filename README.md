# LiveStream
Host a live stream of a video for shared viewing, for 1 cent an hour, through digital ocean

Requires python2.7

Requires ffmpeg if you want the script to stream for you (The `play` command). Otherwise, [VLC](https://www.videolan.org/vlc/index.html) or [OBS](https://obsproject.com/) can be used instead (use `start_server` and `destroy_server` instead), though I've never personally tried them.

Requires an account with digital ocean, and an [API KEY](https://www.digitalocean.com/community/tutorials/how-to-use-the-digitalocean-api-v2)

ffmeg must be compiled with libass for subtitle conversion. Not necessary if you don't want subs.

View the stream with [VLC](https://www.videolan.org/vlc/index.html) or MPV. Requires **flash** to view the stream.

Only tested on OSX. Should work on any Linux box with no issues. 

Windows is untested, but `start_server` and `destroy_server` subcommands **should** work with no issues. The `play` subcommand may not. 

If it doesn't, run start_server to deploy the server, then use VLC or OBS to create an RTMP stream pointed at the provided url. Just make sure to call destroy_server when you're done.

Only tested on OSX. Should work on Linux with no issues. Might work on Windows (particularly the ffmpeg call might break). OBS/VLC would probably be more convenient for Windows users.

## Install
OSX (brew) install:
```sh
brew install ffmpeg --with-libass # this will take like 30 min
pip install click, requests
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

Example:

Start the Server, stream the movie, stop the server
```
$ python spawn.py play --subs ~/Downloads/KungFu/Police-Story-3-720p.mkv

Attempt #1/3: Starting up the VM...
VM at ip 104.236.62.99 is now active

Attempt #7/20: Waiting for nginx to finish compiling...

Running command: ffmpeg -re -loglevel warning -i /Users/setr/Downloads/KungFu/Police-Story-3-720p.mkv -c:v libx264 -c:a libmp3lame -filter:v subtitles=/Users/setr/Downloads/KungFu/Police-Story-3-720p.mkv -ar 44100 -ac 1 -f flv rtmp://104.236.62.99/live

The stream is now live at rtmp://104.236.62.99/live
Enjoy!
```

Start the server and set it up for streaming, but don't stream anything
```
$ python spawn.py start_server

Starting server
VM at ip 104.236.192.177 is now active
104.236.192.177
Attempt #7/20: Waiting for nginx to finish compiling...
Server is ready! Point an RTMP stream at rtmp://104.236.192.177/live
```

Destroy any running servers created by this script
```
$ python spawn.py destroy_server

Attempt #1/3: Trying to kill VM with tag f48dff2e-7fb7-49e8-b9bf-2013c9deff90...
```



## Important Notes
* If you cancel the script early, or something goes wrong, make sure to go to digitalocean.com and destroy the VM yourself (named StreamServer). The script **does not** ensure multiple servers are not created. Each server will cost you $5/monthly if you never close them.
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
  * If you cancel the script early, or something goes wrong, make sure to go to digitalocean.com and destroy the VM yourself (named StreamServer). The script **does not** ensure multiple servers are not created. Each server will cost you $5/monthly if you never close them.

This means that you have one input stream, from the local computer to the digital ocean vm, and `n` output streams for `n` viewers. 

In testing, a 1.5 GB h264, mkv video converted to 750 MB. So with 10 viewers, I had a total traffic of (n + 1) * 750MB = (10 + 1) * 750 = 8250 MB = ~8GB network traffic.

Digital Ocean has a limit of 1 Terabyte of network traffic monthly for your account, which will restrict the total number of movies you can play monthly. According to other people, but I haven't tested myself, it has an upload speed of 330Mb/s, which will limit the number of viewers simultaneously. 

For most people, this is probably more than reasonable. 

## Future
Provide instructions for streaming through [VLC](https://www.videolan.org/vlc/index.html) and [OBS](https://obsproject.com/)

Optionally start up an HLS/Dash feed instead (or alongside?) RTMP, and I guess a webpage to go with it.

FFMPEG can apparently take a url as input, so we might as well support that too (currently blocked because it checks if video is a valid file)

Only accept streams from ip address that ran this script, or from a list of given IP's.

Maybe maintain a pre-compiled version of Nginx in this repo, to speed up deployment. 

Make the script installable.

Add proper logging and loglevels
