<b>genRSS</b>
=========

### What is genRSS?
genRSS takes a directory hosted on your website and generates an RSS 2 feed for all media files within the directory. It can operate recursively and look for media files in sub directories. Media files can also be restricted to a given set of extensions.

### How to use genRSS?
Suppose you have a web server and a website hosted on that server. genRSS can be run on a given directory on the website to generate a feed from media files in the directory so you can access them with a podcast reader.

The following command launches an HTTP server that serves the current directory

    python -m SimpleHTTPServer

The server will be listening on port 8000 (default). You can also spicify the port as an argument:

    python -m SimpleHTTPServer 8080

Go to a web browser and type: http://localhost:8080/ . You should get a web page listing of all elements in current directory .

Place the test media directory (contains fake media files) in the directory served by SimpleHTTPServerer and refresh the web page. You should now see and be able to browse the media folder.

Now place genRSS.py into the same directory and try the following examples.

### Examples:

**_Generate a podcast from media files in "media"_**

    python genRSS.py -d test/media --host localhost:8080 --title "My Podcast" --description "My Podcast Description"  -o feed-1.rss

feed-1.rss should now be visible on the web page. You can visit it or open it with a podcast reader.


**_Generate a podcast from media files in "media" and its subdirectories_**

    python genRSS.py --recursive -d test/media --host localhost:8080 --title "My Podcast" --description "My Podcast Description" -o feed-1.rss

**_Generate a podcast from MP3 and OGG files in "media" and its subdirectories_**

    python genRSS.py -e "mp3,ogg" -d test/media --host localhost:8080 --title "My Podcast" --description "My Podcast Description" --recursive -o feed-1.rss


### Access your poscast from another machine/device:

localhost:8080 are you host name and your http server port respectively. This pair is automatically used by genRSS.py as prefix for items in the generated podcast. Alternatively, you can use your machine's IP address instead of localhost. This is particularly useful if you want to access your podcast from another machine or a mobile device that share the same network.

**Example:**

    python genRSS.py -e "mp3,ogg" -d test/media --host 192.168.1.5:8080 --title "My Podcast" --description "My Podcast Description" --recursive -o feed-1.rss

### Tests

To run tests type:

    python genRSS.py --run-tests

or in verbose mode:

    python genRSS.py --run-tests -v

Wiki: https://github.com/amsehili/genRSS/wiki
