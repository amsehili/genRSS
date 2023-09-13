#!/usr/bin/env python3
# encoding: utf-8
"""
genRSS -- generate an RSS 2.0 feed from media files in a directory.

@author:     Amine SEHILI
@copyright:  2014-2023 Amine SEHILI
@license:    MIT
@contact:    amine.sehili <AT> gmail.com
@deffield    updated: September 13th 2023
"""

import sys
import os
import time
import random
import urllib
import urllib.parse
import argparse
from xml.sax import saxutils

from util import (
    get_files,
    file_to_item,
)

__all__ = []
__version__ = "0.3.0"
__date__ = "2014-11-01"
__updated__ = "2023-09-13"

DEBUG = 0
TESTRUN = 0
PROFILE = 0


def main(argv=None):
    program_name = os.path.basename(sys.argv[0])
    program_usage = "genRSS -d directory [OPTIONS]"
    program_longdesc = "Generates an RSS feed from files in a directory"

    if argv is None:
        argv = sys.argv[1:]
    try:
        parser = argparse.ArgumentParser(
            usage=program_usage,
            description=program_longdesc,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        parser.add_argument(
            "--version", "-v", action="version", version=__version__
        )
        parser.add_argument(
            "-d",
            "--dirname",
            dest="dirname",
            help="Directory to look for media files in.\n"
            "This directory name will be appended to the host name\n"
            "to create absolute paths to your media files.",
            metavar="DIRECTORY",
        )
        parser.add_argument(
            "-r",
            "--recursive",
            dest="recursive",
            help="Look for media files recursively in subdirectories\n"
            "[default: False]",
            action="store_true",
            default=False,
        )

        parser.add_argument(
            "-e",
            "--extensions",
            dest="extensions",
            help=(
                "A comma separated list of extensions (e.g. mp3,mp4,avi,ogg)"
                "\n[default: all files]"
            ),
            type=str,
            default=None,
            metavar="STRING",
        )

        parser.add_argument(
            "-o",
            "--out",
            dest="outfile",
            help="Output RSS file [default: stdout]",
            metavar="FILE",
        )
        parser.add_argument(
            "-H",
            "--host",
            dest="host",
            help="Host name (or IP address), possibly with a protocol\n"
            "(default: http) a port number and the path to the base\n"
            "directory where your media directory is located.\n"
            "Examples of host names:\n"
            " - http://localhost:8080 [default]\n"
            " - mywebsite.com/media/JapaneseLessons\n"
            " - mywebsite\n"
            " - 192.168.1.12:8080\n"
            " - http://192.168.1.12/media/JapaneseLessons\n",
            default="http://localhost:8080",
            metavar="URL",
        )
        parser.add_argument(
            "-i",
            "--image",
            dest="image",
            help="Absolute or relative URL for feed's image [default: None]",
            default=None,
            metavar="URL",
        )

        parser.add_argument(
            "-M",
            "--metadata",
            dest="use_metadata",
            help="Use media files' metadata to extract item title [default: False]",
            action="store_true",
            default=False,
        )

        parser.add_argument(
            "-t",
            "--title",
            dest="title",
            help="Title of the podcast [default: use directory name as title]",
            default=None,
            metavar="STRING",
        )
        parser.add_argument(
            "-p",
            "--description",
            dest="description",
            help="Description of the podcast [default: None]",
            default=None,
            metavar="STRING",
        )
        parser.add_argument(
            "-C",
            "--sort-creation",
            dest="sort_creation",
            help="Sort files by date of creation instead of file name (default)",
            action="store_true",
            default=False,
        )
        # process options
        opts = parser.parse_args(argv)

        if opts.dirname is None or opts.host is None:
            raise Exception(
                "\n".join(
                    [
                        "Usage: python %s -d directory -H hostname [-o output -r]"
                        % (program_name),
                        "For more information run %s --help\n" % (program_name),
                    ]
                )
            )

        if not os.path.isdir(opts.dirname) or not os.path.exists(opts.dirname):
            raise Exception(
                "\n".join(
                    [
                        "Cannot find directory {0}",
                        "--dirname must be a path to an existing directory",
                    ]
                ).format(opts.dirname)
            )

        dirname = opts.dirname
        if dirname[-1] != os.sep:
            dirname += os.sep
        host = opts.host
        if host[-1] != "/":
            host += "/"

        if not host.lower().startswith(
            "http://"
        ) and not host.lower().startswith("https://"):
            host = "http://" + host

        title = ""
        description = ""
        link = host
        if opts.outfile is not None:
            if link[-1] == "/":
                link += opts.outfile
            else:
                link += "/" + opts.outfile

        if opts.title is None:
            title = os.path.split(dirname[:-1])[-1]
        else:
            title = opts.title

        if opts.description is not None:
            description = opts.description

        # get the list of the desired files
        if opts.extensions is not None:
            opts.extensions = [e for e in opts.extensions.split(",") if e != ""]
        file_names = get_files(
            dirname, extensions=opts.extensions, recursive=opts.recursive
        )
        if len(file_names) == 0:
            sys.stderr.write(
                "No media files on directory '%s'\n" % (opts.dirname)
            )
            sys.exit(0)

        if opts.sort_creation:
            # sort files by date of creation if required
            # get files date of creation in seconds
            pub_dates = [os.path.getmtime(f) for f in file_names]
            # most feed readers will use pubDate to sort items even if they are
            # not sorted in the output file for readability, we also sort fileNames
            # according to pubDates in the feed.
            sorted_files = sorted(
                zip(file_names, pub_dates), key=lambda f: -f[1]
            )

        else:
            # In order to have feed items sorted by name, we give them artificial
            # pubDates. file_names are already sorted (natural order), so we assume
            # that the first item is published now and the n-th item (now - (n))
            # minutes and f seconds ago, where f is a random float between 0 and 10
            now = time.time()
            pub_dates = [
                now - (60 * 60 * 24 * d + (random.random() * 10))
                for d in range(len(file_names))
            ]
            sorted_files = zip(file_names, pub_dates)

        # write dates in RFC 822 format
        sorted_files = (
            (
                f[0],
                time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(f[1])),
            )
            for f in sorted_files
        )

        # build items
        items = [
            file_to_item(host, fname, pub_date, opts.use_metadata)
            for fname, pub_date in sorted_files
        ]

        if opts.outfile is not None:
            outfp = open(opts.outfile, "w")
        else:
            outfp = sys.stdout

        outfp.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        outfp.write(
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/">\n'
        )
        outfp.write("   <channel>\n")
        outfp.write(
            '      <atom:link href="{0}" rel="self" type="application/rss+xml" />\n'.format(
                link
            )
        )
        outfp.write("      <title>{0}</title>\n".format(saxutils.escape(title)))
        outfp.write(
            "      <description>{0}</description>\n".format(description)
        )
        outfp.write("      <link>{0}</link>\n".format(link))

        if opts.image is not None:
            if opts.image.lower().startswith(
                "http://"
            ) or opts.image.lower().startswith("https://"):
                imgurl = opts.image
            else:
                imgurl = urllib.parse.quote(host + opts.image, ":/")

            outfp.write("      <image>\n")
            outfp.write("         <url>{0}</url>\n".format(imgurl))
            outfp.write(
                "         <title>{0}</title>\n".format(saxutils.escape(title))
            )
            outfp.write("         <link>{0}</link>\n".format(link))
            outfp.write("      </image>\n")

        for item in items:
            outfp.write(item + "\n")

        outfp.write("")
        outfp.write("   </channel>\n")
        outfp.write("</rss>\n")

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

        profile_filename = "genRSS_profile.txt"
        cProfile.run("main()", profile_filename)
        stats_file = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=stats_file)
        stats = p.strip_dirs().sort_stats("cumulative")
        stats.print_stats()
        stats_file.close()
        sys.exit(0)
    sys.exit(main())
