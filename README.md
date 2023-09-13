# genRSS

`genRSS` is a tool to create an RSS 2.0 feed from media files in a directory.
Files can be looked for recursively in subdirectories and can be restricted to a
given set of extensions.

## Installation

    pip install mutagen eyed3 generss

## Determining file duration

To include media file duration in your feeds (using the `<itunes:duration>` tag),
`genRSS` use tries the following options.

- `mutagen`: a python package installed alongside `genRSS` that can deal with
audio and video files.
- `sox`: can only handle audio files, runs faster than `ffprobe`.
- `ffprobe`: normally installed with `ffmpeg`, can deal with audio and video files
but it is the slowest of the three options.

In any case, if `genRSS` fails to get media file duration with one tool, it'll
fall back to the next one. If none of these tools is installed or if file duration
cannot be obtained, no `<itunes:duration>` tag will be inserted.


## Usage options

```
  -d DIRECTORY, --dirname DIRECTORY
                        Directory to look for media files in.
                        This directory name will be appended to the host name
                        to create absolute paths to your media files.
  -r, --recursive       Look for media files recursively in subdirectories
                        [Default:False]
  -e STRING, --extensions STRING
                        A comma separated list of extensions (e.g. mp3,mp4,avi,ogg)
                        [Default: all files]
  -o FILE, --out FILE   Output RSS file [default: stdout]
  -H URL, --host URL    Host name (or IP address), possibly with a protocol
                        (default: http) a port number and the path to the base
                        directory where your media directory is located.
                        Examples of host names:
                         - http://localhost:8080 [default]
                         - mywebsite.com/media/JapaneseLessons
                         - mywebsite
                         - 192.168.1.12:8080
                         - http://192.168.1.12/media/JapaneseLessons
  -i URL, --image URL   Absolute or relative URL for feed's image [default: None]
  -M, --metadata        Use media files' metadata to extract item title [default: False]
  -t STRING, --title STRING
                        Title of the podcast [Default: use directory name as title]
  -p STRING, --description STRING
                        Description of the podcast [Default:None]
  -C, --sort-creation   Sort files by date of creation instead of name (default)
  -v, --verbose         set verbose [default: False]
```


### License
MIT