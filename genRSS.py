#!/usr/bin/env python3
# encoding: utf-8
'''
genRSS -- generate a RSS 2 feed from media files in a directory.

@author:     Amine SEHILI
@copyright:  2014-2020 Amine Sehili
@license:    MIT
@contact:    amine.sehili <AT> gmail.com
@deffield    updated: April 21st 2020
'''

import sys
import os
import glob
import fnmatch
import time
import urllib
import urllib.parse
import mimetypes
import argparse


from optparse import OptionParser

__all__ = []
__version__ = 0.1
__date__ = '2014-11-01'
__updated__ = '2020-04-21'

DEBUG = 0
TESTRUN = 0
PROFILE = 0


def getFiles(dirname, extensions=None, recursive=False):
    '''
    Return the list of files (relative paths, starting from dirname) in a given directory.

    Unless a list of the desired file extensions is given, all files in dirname are returned.
    If recursive = True, also look for files in sub directories of direname.

    Parameters
    ----------
    dirname : string
              path to a directory under the file system.

    extensions : list of string
                 Extensions of the accepted files.
                 Default = None (i.e. return all files).

    recursive : bool
                If True, recursively look for files in sub directories.
                Default = False.

    Returns
    -------
    selectedFiles : list
                A list of file paths.

    Examples
    --------
    >>> import os
    >>> m = "test{0}media{0}".format(os.sep)
    >>> expected = "['{0}1.mp3', '{0}1.mp4', '{0}1.ogg', '{0}2.MP3']".format(m)
    >>> str(getFiles("{0}".format(m))) == expected
    True
    >>> expected = "['{0}1.mp3', '{0}1.mp4', '{0}1.ogg', '{0}2.MP3', '{0}subdir_1{1}2.MP4', "
    >>> expected += "'{0}subdir_1{1}3.mp3', '{0}subdir_1{1}4.mp3', '{0}subdir_2{1}4.mp4', "
    >>> expected += "'{0}subdir_2{1}5.mp3', '{0}subdir_2{1}6.mp3']"
    >>> str(getFiles("{0}".format(m), recursive=True)) == expected.format(m, os.sep)
    True
    >>> expected = "['{0}1.mp3', '{0}2.MP3']".format(m)
    >>> str(getFiles("{0}".format(m), extensions=["mp3"])) == expected
    True
    >>> expected = "['{0}1.mp3', '{0}1.ogg', '{0}2.MP3', '{0}subdir_1{1}3.mp3', "
    >>> expected += "'{0}subdir_1{1}4.mp3', '{0}subdir_2{1}5.mp3', '{0}subdir_2{1}6.mp3']"
    >>> str(getFiles("{0}".format(m), extensions=["mp3", "ogg"], recursive=True)) == expected.format(m, os.sep)
    True
    >>> expected = "['{0}1.mp4', '{0}subdir_1{1}2.MP4', '{0}subdir_2{1}4.mp4']".format(m, os.sep)
    >>> str(getFiles("{0}".format(m), extensions=["mp4"], recursive=True)) == expected
    True
    '''

    if dirname[-1] != os.sep:
        dirname += os.sep

    selectedFiles = []
    allFiles = []
    if recursive:
        for root, dirs, filenames in os.walk(dirname):
                for name in filenames:
                    allFiles.append(os.path.join(root, name))
    else:
        allFiles = [f for f in glob.glob(dirname + "*") if os.path.isfile(f)]

    if extensions is not None:
        for ext in set([e.lower() for e in extensions]):
            selectedFiles += [n for n in allFiles if fnmatch.fnmatch(n.lower(), "*{0}".format(ext))]
    else:
        selectedFiles = allFiles

    return sorted(set(selectedFiles))


def buildItem(link, title, guid = None, description="", pubDate=None, indent = "   ", extraTags=None):
    '''
    Generate a RSS 2 item and return it as a string.

    Parameters
    ----------
    link : string
           URL of the item.

    title : string
            Title of the item.

    guid : string
           Unique identifier of the item. If no guid is given, link is used as the identifier.
           Default = None.

   description : string
                 Description of the item.
                 Default = ""

    pubDate : string
              Date of publication of the item. Should follow the RFC-822 format,
              otherwise the feed will not pass a validator.
              This method doses (yet) not check the compatibility of pubDate.
              Here are a few examples of correct RFC-822 dates:

              - "Wed, 02 Oct 2002 08:00:00 EST"
              - "Mon, 22 Dec 2014 18:30:00 +0000"

              You can use the following code to gererate a RFC-822 valid time:
              time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(time.time()))
              Default = None (no pubDate tag will be added to the generated item)

    indent : string
             A string of white spaces used to indent the elements of the item.
             3 * len(indent) white spaces will be left before <guid>, <link>, <title> and <description>
             and 2 * len(indent) before item.

    extraTags : a list of dictionaries
                Each dictionary contains the following keys
                - "na1me": name of the tag (mandatory)
                - "value": value of the tag (optional)
                - "params": string or list of string, parameters of the tag (optional)

                Example:
                -------
                Either of the following two dictionaries:
                   {"name" : enclosure, "value" : None, "params" : 'url="file.mp3" type="audio/mpeg" length="1234"'}
                   {"name" : enclosure, "value" : None, "params" : ['url="file.mp3"', 'type="audio/mpeg"', 'length="1234"']}
                will give this tag:
                   <enclosure url="file.mp3" type="audio/mpeg" length="1234"/>

                whereas this dictionary:
                   {"name" : "aTag", "value" : "aValue", "params" : None}
                would give this tag:
                   <aTag>aValue</aTag>

    Returns
    -------
    A string representing a RSS 2 item.

    Examples
    --------
    >>> item = buildItem("my/web/site/media/item1", title = "Title of item 1", guid = "item1",
    ...                  description="This is item 1", pubDate="Mon, 22 Dec 2014 18:30:00 +0000",
    ...                  indent = "   ")
    >>> print(item)
          <item>
             <guid>item1</guid>
             <link>my/web/site/media/item1</link>
             <title>Title of item 1</title>
             <description>This is item 1</description>
             <pubDate>Mon, 22 Dec 2014 18:30:00 +0000</pubDate>
          </item>

    >>> item = buildItem("my/web/site/media/item2", title = "Title of item 2", indent = " ",
    ...                  extraTags=[{"name" : "itunes:duration" , "value" : "06:08"}])
    >>> print(item)
      <item>
       <guid>my/web/site/media/item2</guid>
       <link>my/web/site/media/item2</link>
       <title>Title of item 2</title>
       <description></description>
       <itunes:duration>06:08</itunes:duration>
      </item>

    >>> item = buildItem("my/web/site/media/item2", title = "Title of item 2", indent = " ",
    ...                  extraTags=[{"name" : "enclosure" ,
    ...                              "params" : 'url="http://example.com/media/file.mp3"'
    ...                                         ' type="audio/mpeg" length="1234"'}])
    >>> print(item)
      <item>
       <guid>my/web/site/media/item2</guid>
       <link>my/web/site/media/item2</link>
       <title>Title of item 2</title>
       <description></description>
       <enclosure url="http://example.com/media/file.mp3" type="audio/mpeg" length="1234"/>
      </item>

    >>> item = buildItem("my/web/site/media/item2", title = "Title of item 2", indent = " ",
    ...                  extraTags= [{"name" : "enclosure", "value" : None,
    ...                               "params" :  ['url="file.mp3"', 'type="audio/mpeg"',
    ...                                            'length="1234"']}])
    >>> print(item)
      <item>
       <guid>my/web/site/media/item2</guid>
       <link>my/web/site/media/item2</link>
       <title>Title of item 2</title>
       <description></description>
       <enclosure url="file.mp3" type="audio/mpeg" length="1234"/>
      </item>
    '''

    if guid is None:
        guid = link

    guid =  "{0}<guid>{1}</guid>\n".format(indent * 3, guid)
    link = "{0}<link>{1}</link>\n".format(indent * 3, link)
    title = "{0}<title>{1}</title>\n".format(indent * 3, title)
    descrption = "{0}<description>{1}</description>\n".format(indent * 3, description)

    if pubDate is not None:
        pubDate = "{0}<pubDate>{1}</pubDate>\n".format(indent * 3, pubDate)
    else:
        pubDate = ""

    extra = ""
    if extraTags is not None:
        for tag in extraTags:
            if tag is None:
                continue

            name = tag["name"]
            value = tag.get("value", None)
            params = tag.get("params", '')
            if params is None:
               params = ''
            if isinstance(params, (list)):
               params = " ".join(params)
            if len(params) > 0:
               params = " " + params

            extra += "{0}<{1}{2}".format(indent * 3, name, params)
            extra += "{0}\n".format("/>" if value is None else ">{0}</{1}>".format(value, name))

    return "{0}<item>\n{1}{2}{3}{4}{5}{6}{0}</item>".format(indent * 2, guid, link, title,
                                                            descrption, pubDate, extra)


def fileToItem(host, fname, pubDate):
    '''
    Inspect a file name to determine what kind of RSS item to build, and
    return the built item.

    Parameters
    ----------
    host : string
           The hostname and directory to use for the link.

    fname : string
            File name to inspect.

    pubDate : string
              Publication date in RFC 822 format.

    Returns
    -------
    A string representing an RSS item, as with buildItem.

    Examples
    --------
    >>> print(fileToItem('example.com/', 'test/media/1.mp3', 'Mon, 16 Jan 2017 23:55:07 +0000'))
          <item>
             <guid>example.com/test/media/1.mp3</guid>
             <link>example.com/test/media/1.mp3</link>
             <title>1.mp3</title>
             <description>1.mp3</description>
             <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
             <enclosure url="example.com/test/media/1.mp3" type="audio/mpeg" length="0"/>
          </item>
    >>> print(fileToItem('example.com/', 'test/invalid/checksum.md5', 'Mon, 16 Jan 2017 23:55:07 +0000'))
          <item>
             <guid>example.com/test/invalid/checksum.md5</guid>
             <link>example.com/test/invalid/checksum.md5</link>
             <title>checksum.md5</title>
             <description>checksum.md5</description>
             <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
          </item>
    >>> print(fileToItem('example.com/', 'test/invalid/windows.exe', 'Mon, 16 Jan 2017 23:55:07 +0000'))
          <item>
             <guid>example.com/test/invalid/windows.exe</guid>
             <link>example.com/test/invalid/windows.exe</link>
             <title>windows.exe</title>
             <description>windows.exe</description>
             <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
          </item>
    '''

    fileURL = urllib.parse.quote(host + fname.replace("\\", "/"), ":/")
    fileMimeType = mimetypes.guess_type(fname)[0]

    if fileMimeType is not None and ("audio" in fileMimeType or "video" in fileMimeType):
        tagParams = "url=\"{0}\" type=\"{1}\" length=\"{2}\"".format(fileURL, fileMimeType, os.path.getsize(fname))
        enclosure = {"name" : "enclosure", "value" : None, "params": tagParams}
    else:
        enclosure = None

    return buildItem(link=fileURL, title=os.path.basename(fname),
                     guid=fileURL, description=os.path.basename(fname),
                     pubDate=pubDate, extraTags=[enclosure])


def main(argv=None):

    program_name = os.path.basename(sys.argv[0])
    program_version = "v0.1"
    program_build_date = "%s" % __updated__

    program_version_string = '%%prog %s (%s)' % (program_version, program_build_date)
    program_usage = "genRSS -d directory [OPTIONS]"
    program_longdesc = "Generates an RSS feed from files in a directory"
    program_license = "Copyright 2014-2017 Amine SEHILI. Licensed under the MIT License"

    if argv is None:
        argv = sys.argv[1:]
    try:

        parser = argparse.ArgumentParser(usage=program_usage, description=program_longdesc,
                                            formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument("-d", "--dirname", dest="dirname",
                            help="Directory to look for media files in.\n"
                                "This directory name will be appended to the host name\n"
                                "to create absolute paths to your media files.",
                            metavar="DIRECTORY")
        parser.add_argument("-r", "--recursive", dest="recursive",
                            help="Look for media files recursively in sub directories\n"
                                "[Default:False]",
                            action="store_true", default=False)

        parser.add_argument("-e", "--extensions", dest="extensions",
                            help="A comma separated list of extensions (e.g. mp3,mp4,avi,ogg)\n[Default: all files]",
                            type=str, default=None, metavar="STRING")

        parser.add_argument("-o", "--out", dest="outfile", help="Output RSS file [default: stdout]", metavar=   "FILE")
        parser.add_argument("-H", "--host", dest="host", help="Host name (or IP address), possibly with a protocol\n"
                                                                "(default: http) a port number and the path to the base\n"
                                                                "directory where your media directory is located.\n"
                                                                "Examples of host names:\n"
                                                                " - http://localhost:8080 [default]\n"
                                                                " - mywebsite.com/media/JapaneseLessons\n"
                                                                " - mywebsite\n"
                                                                " - 192.168.1.12:8080\n"
                                                                " - http://192.168.1.12/media/JapaneseLessons\n",
                            default="http://localhost:8080",  metavar="URL")
        parser.add_argument("-i", "--image", dest="image",
                            help="Absolute or relative URL for feed's image [default: None]",
                            default = None, metavar="URL")

        parser.add_argument("-t", "--title", dest="title", help="Title of the podcast [Defaule:None]",
                            default=None, metavar="STRING")
        parser.add_argument("-p", "--description", dest="description", help="Description of the podcast [Defaule:None]",
                            default=None, metavar="STRING")
        parser.add_argument("-C", "--sort-creation", dest="sort_creation",
                            help="Sort files by date of creation instead of name (default)",
                            action="store_true", default=False)
        parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                            help="set verbose [default: False]")
        # process options
        opts = parser.parse_args(argv)

        if opts.dirname is None or opts.host is None:
            raise Exception("\n".join(["Usage: python %s -d directory -H hostname [-o output -r]" % (program_name),
                                        "For more information run %s --help\n" % (program_name)]))

        if not os.path.isdir(opts.dirname) or not os.path.exists(opts.dirname):
            raise Exception("\n".join["Cannot find directory {0}",
                            "--direname must be a path to an existing directory".format(opts.dirname)])

        dirname = opts.dirname
        if dirname[-1] != os.sep:
            dirname += os.sep
        host = opts.host
        if host[-1] != '/':
            host += '/'

        if not host.lower().startswith("http://") and not host.lower().startswith("https://"):
            host = "http://" + host

        title = ""
        description = ""
        link = host
        if opts.outfile is not None:
            if link[-1] == '/':
                link += opts.outfile
            else:
                link += '/' + opts.outfile

        if opts.title is not None:
            title = opts.title

        if opts.description is not None:
            description = opts.description

        # get the list of the desired files
        if opts.extensions is not None:
            opts.extensions = [e for e in  opts.extensions.split(",") if e != ""]
        fileNames = getFiles(dirname, extensions=opts.extensions, recursive=opts.recursive)
        if len(fileNames) == 0:
            sys.stderr.write("No media files on directory '%s'\n" % (opts.dirname))
            sys.exit(0)

        if opts.sort_creation:
            # sort files by date of creation if required
            # get files date of creation in seconds
            pubDates = [os.path.getctime(f) for f in fileNames]
            # most feed readers will use pubDate to sort items even if they are not sorted in the output file
            # for readability, we also sort fileNames according to pubDates in the feed.
            sortedFiles = sorted(zip(fileNames, pubDates),key=lambda f: - f[1])

        else:
            # in order to have feed items sorted by name, we give them artificial pubDates
            # fileNames are already sorted (natural order), so we assume that the first item is published now
            # and the n-th item, (now - (n)) minutes and f seconds ago.
            # f is a random number of seconds between 0 and 10 (float)
            now = time.time()
            import random
            pubDates = [now - (60 * 60 * 24 * d + (random.random() * 10)) for d in range(len(fileNames))]
            sortedFiles = zip(fileNames, pubDates)

        # write dates in RFC-822 format
        sortedFiles = ((f[0], time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(f[1]))) for f in sortedFiles)

        # build items
        items = [fileToItem(host, fname, pubDate) for fname, pubDate in sortedFiles]

        if opts.outfile is not None:
            outfp = open(opts.outfile,"w")
        else:
            outfp = sys.stdout

        outfp.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        outfp.write('<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n')
        outfp.write('   <channel>\n')
        outfp.write('      <atom:link href="{0}" rel="self" type="application/rss+xml" />\n'.format(link))
        outfp.write('      <title>{0}</title>\n'.format(title))
        outfp.write('      <description>{0}</description>\n'.format(description))
        outfp.write('      <link>{0}</link>\n'.format(link))

        if opts.image is not None:
            if opts.image.lower().startswith("http://") or opts.image.lower().startswith("https://"):
                imgurl = opts.image
            else:
                imgurl = urllib.parse.quote(host + opts.image,":/")

            outfp.write("      <image>\n")
            outfp.write("         <url>{0}</url>\n".format(imgurl))
            outfp.write("         <title>{0}</title>\n".format(title))
            outfp.write("         <link>{0}</link>\n".format(link))
            outfp.write("      </image>\n")

        for item in items:
            outfp.write(item + "\n")

        outfp.write('')
        outfp.write('   </channel>\n')
        outfp.write('</rss>\n')

        if outfp != sys.stdout:
            outfp.close()

    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        return 2


if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
    if TESTRUN or "--run-tests" in sys.argv:
        import doctest
        doctest.testmod()
        sys.exit(0)
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'genRSS_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
