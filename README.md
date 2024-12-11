# genRSS

[![Build Status](https://github.com/amsehili/genRSS/actions/workflows/ci.yml/badge.svg)](https://github.com/amsehili/genRSS/actions/workflows/ci.yml/)

`genRSS` is a tool for generating an RSS 2.0 feed from media files within a
directory. It can search for files recursively in subdirectories and restrict
the search to specific file extensions.

## Installation

Note: Another package named `genrss` already exists on PyPI. To install `genRSS`,
please use `generss` (with an *e* after the *n*):

```bash
pip install generss
```

Once installed, you can run `genRSS` directly from the command line.

## Determining Media File Duration

To include the duration of media files in your feeds (via the
`<itunes:duration>` tag), `genRSS` attempts to determine the duration using the
following tools, in order of preference:

1. **`mutagen`**: a python package (automatically installed if you install
   `genRSS` with `pip`) that supports both audio and video files.
2. **`sox`**: command-line tool, handles only audio files but is faster than
   `ffprobe`.
3. **`ffprobe`**: command-line tool, supports both audio and video files but
   is the slowest option.

If `genRSS` is unable to determine the media file duration using one tool, it
will automatically fall back to the next one in the list. If none of these tools
is available or if the file duration can't be retrieved, the `<itunes:duration>`
tag will not be included in the feed.


## Episode Descriptions

Text files with a `.txt` extension are automatically used to provide
descriptions for media files that share the same name but have different
extensions. As a result, files ending in `.txt` cannot be used as feed items.



## Usage options

Type `genRSS -h` to show the usage options:

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
