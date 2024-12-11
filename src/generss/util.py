import subprocess
import mimetypes
import urllib
import os
import glob
import fnmatch
from xml.sax import saxutils
import eyed3
import mutagen


INDENT = "    "


def _run_command(args):
    """Helper function to run an external program.

    Args:
        args (list): List of arguments. The 1st argument should be the
            program's name.

    Returns:
        output (str): Program output.
    """
    try:
        output = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        return None
    if output.returncode != 0:
        return None
    return output.stdout.decode("utf-8").strip()


def get_duration_mutagen(filename):
    """Get file duration in seconds using mutagen. If mutagen is not installed
    or media file is not valid, return None.

    Args:
        filename (str): Path to a file.

    Returns:
        duration (int): File duration in seconds or None.
    """
    try:
        file = mutagen.File(filename)
    except mutagen.mp3.HeaderNotFoundError:
        return None
    if file is not None:
        return round(file.info.length)


def get_duration_sox(filename):
    """Get file duration in seconds using sox. If sox is not installed or media
    file is not valid, return None.

    Args:
        filename (str): Path to a file.

    Returns:
        duration (int): File duration in seconds or None if no duration could
            be exracted.
    """
    duration_str = _run_command(["soxi", "-D", filename])
    if duration_str is not None:
        try:
            return round(float(duration_str))
        except ValueError:
            return None


def get_duration_ffprobe(filename):
    """Get file duration in seconds using ffprobe. If ffprobe is not installed
    or media file is not valid, return None.

    Args:
        filename (str): Path to a file.

    Returns:
        duration (int): File duration in seconds or None if no duration could be
            extracted.
    """
    duration_str = _run_command(
        [
            "ffprobe",
            "-i",
            filename,
            "-show_entries",
            "format=duration",
            "-v",
            "quiet",
            "-of",
            "csv=p=0",
        ]
    )
    if duration_str is not None:
        try:
            return round(float(duration_str))
        except ValueError:
            return None


def get_description(file_path):
    """
    Get description and summary from a .txt file with the same base name as the
    media file.
    """
    txt_file = f"{os.path.splitext(file_path)[0]}.txt"
    if os.path.exists(txt_file):
        with open(txt_file, "r", encoding="utf-8") as fp:
            return fp.read().strip()
    return None


def file_to_item(host, fname, pub_date, use_metadata=False):
    """
    Inspect a file name to determine what kind of RSS item to build, and
    return the built item.


    Args:
        host (str): The hostname and directory to use for the link.

        fname (str): File name to inspect.

        pub_date (str): Publication date in RFC 822 format.

    Returns:
        A string representing an RSS item, as with build_item.

    Example:
        >>> print(file_to_item('example.com/', 'tests/media/1.mp3', 'Mon, 16 Jan 2017 23:55:07 +0000'))
              <item>
                 <guid>example.com/tests/media/1.mp3</guid>
                 <link>example.com/tests/media/1.mp3</link>
                 <title>1</title>
                 <description>1</description>
                 <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
                 <enclosure url="example.com/tests/media/1.mp3" type="audio/mpeg" length="0"/>
              </item>
    """
    file_URL = urllib.parse.quote(host + fname.replace("\\", "/"), ":/")
    file_mime_type = mimetypes.guess_type(fname)[0]
    tags = []

    if file_mime_type is not None and (
        "audio" in file_mime_type
        or "video" in file_mime_type
        or "image" in file_mime_type
    ):
        tagParams = 'url="{0}" type="{1}" length="{2}"'.format(
            file_URL, file_mime_type, os.path.getsize(fname)
        )
        enclosure = {"name": "enclosure", "value": None, "params": tagParams}
        tags.append(enclosure)

    title = get_title(fname, use_metadata)
    # Fetch description from a corresponding .txt file
    description = get_description(fname)
    if description is None:
        description = title

    duration = get_duration(fname)
    if duration is not None:
        tags.append({"name": "itunes:duration", "value": str(duration)})

    return build_item(
        link=file_URL,
        title=title,
        guid=file_URL,
        description=description,
        pub_date=pub_date,
        extra_tags=tags,
    )


def get_title(filename, use_metadata=False):
    """
    Get item title from file. If use_metadata is True, try reading title from
    metadata otherwise return file name as the title (without extension).

    Args:
        filename (str): Path to a file.

        use_metadata (bool): Whether to use metadata. Default: False.

    Returns:
        title (str): Item title.
    """
    if use_metadata:
        try:
            # file with ID3 tags
            meta = eyed3.load(filename)
            if meta and meta.tag is not None:
                return meta.tag.title
        except ImportError:
            pass

        try:
            import mutagen
            from mutagen import id3, mp4, easyid3, easymp4
            from mutagen.mp3 import HeaderNotFoundError

            try:
                # file with ID3 tags
                title = easyid3.EasyID3(filename)["title"]
                if title:
                    return title[0]
            except (id3.ID3NoHeaderError, KeyError):
                try:
                    # file with MP4 tags
                    title = easymp4.EasyMP4(filename)["title"]
                    if title:
                        return title[0]
                except (mp4.MP4StreamInfoError, KeyError):
                    try:
                        # other media types
                        meta = mutagen.File(filename)
                        if meta is not None:
                            title = meta["title"]
                            if title:
                                return title[0]
                    except (KeyError, HeaderNotFoundError):
                        pass
        except ImportError:
            pass

    # fallback to filename as a title, remove extension though
    filename = os.path.basename(filename)
    title, _ = os.path.splitext(filename)
    return title


def get_duration(filename):
    """
    Get item duration from media file using mutagen, sox or ffprobe in that
    order. mutagen is tried first because it's a python package (so it doesn't
    require running an external process), sox is tried before ffprobe because
    it's faster, easier to install and return 0 for empty files.


    According to both Google and Apple, many formats are supported by the
    <itunes:duration> tag such qs hh:mm:ss, mm:ss, or just the total number of
    seconds as an integer. For more information see:

    https://support.google.com/podcast-publishers/answer/9889544?hl=en#recommended_episode
    https://help.apple.com/itc/podcasts_connect/#/itcb54353390

    Args:
        filename (str): Path to a file.

    Returns:
        duration (int): The duration as the number of seconds or None.
    """
    duration = get_duration_mutagen(filename)
    if duration is not None:
        return duration

    duration = get_duration_sox(filename)
    if duration is not None:
        return duration

    return get_duration_ffprobe(filename)


def make_description(description):
    """Make <description> and <itunes:summary> tags, handling multiline text."""

    if description is None:
        description = ""
    lines = [line for line in description.split("\n") if line]
    if not lines:
        description = f"{INDENT * 3}<description></description>"
        itunes_summary = f"{INDENT * 3}<itunes:summary></itunes:summary>"

    elif len(lines) == 1:
        desc_text = saxutils.escape(lines[0].strip())
        description = f"{INDENT * 3}<description>{desc_text}</description>"
        itunes_summary = f"{INDENT * 3}<itunes:summary>{desc_text}</itunes:summary>"
    else:
        # multiline description
        description = [f"{INDENT * 4}{line}" for line in lines]
        description = "\n".join(description)
        desc_text = saxutils.escape(description)

        description = (
            f"{INDENT * 3}<description>\n{desc_text}\n{INDENT * 3}</description>"
        )
        itunes_summary = (
            f"{INDENT * 3}<itunes:summary>\n{desc_text}\n{INDENT * 3}</itunes:summary>"
        )

    return description, itunes_summary


def build_extra_tag(tag):
    name = tag["name"]
    value = tag.get("value", None)
    params = tag.get("params", "")
    if params is None:
        params = ""
    if isinstance(params, (list)):
        params = " ".join(params)
    if len(params) > 0:
        params = " " + params

    tag = f"{INDENT * 3}<{name}{params}"
    if value is None:
        tag += "/>"
    else:
        tag += f">{value}</{name}>".format(value, name)
    return tag


def build_item(
    link,
    title,
    guid=None,
    description=None,
    pub_date=None,
    extra_tags=None,
):
    """
    Generate an RSS 2.0 item and return it as a string.

    Args:
        link (str): URL of the item.

        title (str): Title of the item.

        guid (str): Unique identifier of the item. If no guid is given, 'link'
            is used as the identifier. Default = None.

       description (str): Description of the item.
            Default = "".

    pub_date (str): Date of publication of the item. Should follow the RFC 822 format,
            otherwise the feed will not pass a validator.
            This method does not (yet) check the compatibility of pubDate.
            Here are a few examples of correct RFC 822 dates:


            - "Wed, 02 Oct 2002 08:00:00 EST"
            - "Mon, 22 Dec 2014 18:30:00 +0000"

            You can use the following code to gererate an RFC 822 valid time:
            time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(time.time()))
            Default = None (no pubDate tag will be added to the generated item)


    extra_tags (list of dictionaries): Each dictionary contains the following keys
        - "name": name of the tag (mandatory)
        - "value": value of the tag (optional)
        - "params": string or list of strings, parameters of the tag (optional)

        Example:
            Either of the following two dictionaries:
                {"name" : "enclosure", "value" : None, "params" : 'url="file.mp3" type="audio/mpeg" length="1234"'}
                {"name" : "enclosure", "value" : None, "params" : ['url="file.mp3"', 'type="audio/mpeg"', 'length="1234"']}
            will give this tag:
                <enclosure url="file.mp3" type="audio/mpeg" length="1234"/>

            whereas this dictionary:
                {"name" : "aTag", "value" : "aValue", "params" : None}
            would give this tag:
                <aTag>aValue</aTag>

    Returns:
        A string representing an RSS 2.0 item.

    Examples:
        >>> item = build_item("my/web/site/media/item1", title = "Title of item 1", guid = "item1",
        ...                  description="This is item 1", pub_date="Mon, 22 Dec 2014 18:30:00 +0000")
        >>> print(item)
              <item>
                 <guid>item1</guid>
                 <link>my/web/site/media/item1</link>
                 <title>Title of item 1</title>
                 <description>This is item 1</description>
                 <pubDate>Mon, 22 Dec 2014 18:30:00 +0000</pubDate>
              </item>
    """
    if guid is None:
        guid = link

    description, itunes_summary = make_description(description)
    if "<description></description>" in description:
        # empty description, use title instead
        description, itunes_summary = make_description(title)

    guid = f"{INDENT * 3}<guid>{guid}</guid>"
    link = f"{INDENT * 3}<link>{link}</link>"
    title = f"{INDENT * 3}<title>{saxutils.escape(title)}</title>"

    tags = [
        f"{INDENT * 2}<item>",
        guid,
        link,
        title,
        description,
        itunes_summary,
    ]

    if pub_date is not None:
        pub_date = f"{INDENT * 3}<pubDate>{pub_date}</pubDate>"
        tags.append(pub_date)

    if extra_tags is None:
        extra_tags = []

    extra_tags = [build_extra_tag(tag) for tag in extra_tags]

    tags.extend(extra_tags)
    tags.append(f"{INDENT * 2}</item>")

    return "\n".join(tags)


def get_files(dirname, extensions=None, recursive=False, followlinks=False):
    """
    Return the list of files (relative paths, starting from dirname) in a given
    directory. Files ending with .txt are ignored as they can be used to store
    the description of media files.

    Unless a list of the desired file extensions is given, all files in dirname
    are returned. If recursive is true, also look for files in subdirectories
    of dirname.

    Args:
        dirname (str): path to a directory under the file system.

        extensions (list of str): Extensions of the accepted files.
            Default = None (i.e. return all files).

        recursive (bool): If True, recursively look for files in subdirectories.
            Default = False.

        followlinks (bool): If True, follow symbolic links to directories during
            recursive scan. Default = False.

    Returns:
        selected_files (list): A list of file paths.

    Examples:
        >>> import os
        >>> media_dir = os.path.join("tests", "media")
        >>> files =  ['1.mp3', '1.mp4', '1.ogg', '2.MP3', 'flac_with_tags.flac', 'mp3_with_tags.mp3']
        >>> expected = [os.path.join(media_dir, f) for f in files]
        >>> get_files(media_dir) == expected
        True
    """

    if dirname[-1] != os.sep:
        dirname += os.sep

    selected_files = []
    all_files = []
    if recursive:
        for root, dirs, filenames in os.walk(dirname, followlinks=followlinks):
            for name in filenames:
                all_files.append(os.path.join(root, name))
    else:
        all_files = [f for f in glob.glob(dirname + "*") if os.path.isfile(f)]

    if extensions is not None:
        for ext in set(e.lower() for e in extensions):
            selected_files += [
                f for f in all_files if fnmatch.fnmatch(f.lower(), f"*{ext}")
            ]
    else:
        selected_files = all_files

    # remove files ending with .txt
    selected_files = [
        f for f in selected_files if not fnmatch.fnmatch(f.lower(), "*.txt")
    ]

    return sorted(set(selected_files))
