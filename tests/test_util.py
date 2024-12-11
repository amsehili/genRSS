import os
import re

import pytest

from generss.util import build_item, file_to_item, get_duration, get_files, get_title


@pytest.mark.parametrize(
    "filename, use_metadata, expected_title",
    [
        (
            os.path.join("tests", "media", "flac_with_tags.flac"),
            False,
            "flac_with_tags",
        ),
        (
            os.path.join("tests", "media", "flac_with_tags.flac"),
            True,
            "Test FLAC file with tags",
        ),
        (
            os.path.join("tests", "media", "mp3_with_tags.mp3"),
            True,
            "Test media file with ID3 tags",
        ),
    ],
    ids=[
        "flac_without_metadata",
        "flac_with_metadata",
        "mp3_with_metadata",
    ],
)
def test_get_title(filename, use_metadata, expected_title):
    assert get_title(filename, use_metadata) == expected_title


@pytest.mark.parametrize(
    "filename, expected_duration",
    [
        (os.path.join("tests", "silence", "silence_7.14_seconds.ogg"), 7),
        (os.path.join("tests/silence/silence_2.5_seconds.wav"), 2),
        (os.path.join("tests/media/flac_with_tags.flac"), 0),
        (os.path.join("tests/media/1.mp3"), None),
    ],
    ids=[
        "ogg_duration_7.14_seconds",
        "wav_duration_2.5_seconds",
        "empty_flac_duration_0",
        "invalid_mp3_duration",
    ],
)
def test_get_duration(filename, expected_duration):
    assert get_duration(filename) == expected_duration


@pytest.mark.parametrize(
    "link, title, guid, description, pub_date, extra_tags, expected_item",
    [
        (
            "link/to/website/media/item1",
            "Title 1",
            "item1",
            "Description of item 1",
            "Mon, 22 Dec 2014 18:30:00 +0000",
            None,
            """<item>
                    <guid>item1</guid>
                    <link>link/to/website/media/item1</link>
                    <title>Title 1</title>
                    <description>Description of item 1</description>
                    <itunes:summary>Description of item 1</itunes:summary>
                    <pubDate>Mon, 22 Dec 2014 18:30:00 +0000</pubDate>
                </item>""",
        ),
        (
            "link/to/website/media/item1",
            "Title 1",
            "item1",
            "Description line 1\nDescription line 2",
            "Mon, 22 Dec 2014 18:30:00 +0000",
            None,
            """<item>
                    <guid>item1</guid>
                    <link>link/to/website/media/item1</link>
                    <title>Title 1</title>
                    <description> Description line 1\nDescription line 2 </description>
                    <itunes:summary> Description line 1\nDescription line 2 </itunes:summary>
                    <pubDate>Mon, 22 Dec 2014 18:30:00 +0000</pubDate>
                </item>""",
        ),
        (
            "link/to/website/media/item1",
            "Title 1",
            "item1",
            None,
            "Mon, 22 Dec 2014 18:30:00 +0000",
            None,
            """<item>
                    <guid>item1</guid>
                    <link>link/to/website/media/item1</link>
                    <title>Title 1</title>
                    <description>Title 1</description>
                    <itunes:summary>Title 1</itunes:summary>
                    <pubDate>Mon, 22 Dec 2014 18:30:00 +0000</pubDate>
                </item>""",
        ),
        (
            "link/to/website/media/item1",
            "Title 1",
            None,
            "Description of item 1",
            "Mon, 22 Dec 2014 18:30:00 +0000",
            None,
            """<item>
                    <guid>link/to/website/media/item1</guid>
                    <link>link/to/website/media/item1</link>
                    <title>Title 1</title>
                    <description>Description of item 1</description>
                    <itunes:summary>Description of item 1</itunes:summary>
                    <pubDate>Mon, 22 Dec 2014 18:30:00 +0000</pubDate>
                </item>""",
        ),
        (
            "link/to/website/media/item1",
            "Title 1",
            "1234",
            "Description of item 1",
            None,
            None,
            """<item>
                    <guid>1234</guid>
                    <link>link/to/website/media/item1</link>
                    <title>Title 1</title>
                    <description>Description of item 1</description>
                    <itunes:summary>Description of item 1</itunes:summary>
                   </item>""",
        ),
        (
            "link/to/website/media/item1",
            "Title 1",
            "item1",
            "Description of item 1",
            "Mon, 22 Dec 2014 18:30:00 +0000",
            [
                {
                    "name": "tag",
                    "value": None,
                    "params": ['url="file.mp3"', 'type="audio/mpeg"', 'length="1234"'],
                }
            ],
            """<item>
                    <guid>item1</guid>
                    <link>link/to/website/media/item1</link>
                    <title>Title 1</title>
                    <description>Description of item 1</description>
                    <itunes:summary>Description of item 1</itunes:summary>
                    <pubDate>Mon, 22 Dec 2014 18:30:00 +0000</pubDate>
                    <tag url="file.mp3" type="audio/mpeg" length="1234"/>
                </item>""",
        ),
        (
            "link/to/website/media/item1",
            "Title 1",
            "item1",
            "Description of item 1",
            "Mon, 22 Dec 2014 18:30:00 +0000",
            [
                {
                    "name": "tag",
                    "value": None,
                    "params": 'url="file.mp3" type="audio/mpeg" length="1234"',
                }
            ],
            """<item>
                    <guid>item1</guid>
                    <link>link/to/website/media/item1</link>
                    <title>Title 1</title>
                    <description>Description of item 1</description>
                    <itunes:summary>Description of item 1</itunes:summary>
                    <pubDate>Mon, 22 Dec 2014 18:30:00 +0000</pubDate>
                    <tag url="file.mp3" type="audio/mpeg" length="1234"/>
                </item>""",
        ),
        (
            "link/to/website/media/item1",
            "Title 1",
            "item1",
            "Description of item 1",
            "Mon, 22 Dec 2014 18:30:00 +0000",
            [
                {
                    "name": "tag1",
                    "value": None,
                    "params": ['url="file.mp3"', 'type="audio/mpeg"', 'length="1234"'],
                },
                {
                    "name": "tag2",
                    "value": None,
                    "params": 'url="file.mp3" type="audio/mpeg" length="1234"',
                },
            ],
            """<item>
                    <guid>item1</guid>
                    <link>link/to/website/media/item1</link>
                    <title>Title 1</title>
                    <description>Description of item 1</description>
                    <itunes:summary>Description of item 1</itunes:summary>
                    <pubDate>Mon, 22 Dec 2014 18:30:00 +0000</pubDate>
                    <tag1 url="file.mp3" type="audio/mpeg" length="1234"/>
                    <tag2 url="file.mp3" type="audio/mpeg" length="1234"/>
                </item>""",
        ),
        (
            "link/to/website/media/item1",
            "Title 1",
            "item1",
            "Description of item 1",
            "Mon, 22 Dec 2014 18:30:00 +0000",
            [
                {
                    "name": "tag1",
                    "value": "Value1",
                    "params": ['url="file.mp3"', 'type="audio/mpeg"', 'length="1234"'],
                },
                {
                    "name": "tag2",
                    "value": "Value2",
                    "params": None,
                },
            ],
            """<item>
                    <guid>item1</guid>
                    <link>link/to/website/media/item1</link>
                    <title>Title 1</title>
                    <description>Description of item 1</description>
                    <itunes:summary>Description of item 1</itunes:summary>
                    <pubDate>Mon, 22 Dec 2014 18:30:00 +0000</pubDate>
                    <tag1 url="file.mp3" type="audio/mpeg" length="1234">Value1</tag1>
                    <tag2>Value2</tag2>
                </item>""",
        ),
    ],
    ids=[
        "simple",
        "multiline_description",
        "description_None",
        "guid_None",
        "pubDate_None",
        "extra_tags_no_value_params_list",
        "extra_tags_no_value_params_string",
        "extra_tags_multiple_no_value",
        "extra_tags_multiple_with_value",
    ],
)
def test_build_item(
    link,
    title,
    guid,
    description,
    pub_date,
    extra_tags,
    expected_item,
):

    item = build_item(
        link,
        title,
        guid,
        description,
        pub_date,
        extra_tags,
    )

    item = re.sub(r"\s+", " ", item.strip())
    expected_item = re.sub(r"\s+", " ", expected_item.strip())
    assert item == expected_item


@pytest.mark.parametrize(
    "host, fname, pub_date, use_metadata, expected_item",
    [
        (
            "example.com/",
            "tests/media/1.mp3",
            "Mon, 16 Jan 2017 23:55:07 +0000",
            False,
            """<item>
              <guid>example.com/tests/media/1.mp3</guid>
              <link>example.com/tests/media/1.mp3</link>
              <title>1</title>
              <description> Description of 1.mp3.\nThis is a second line.\nAnd a third. </description>
              <itunes:summary> Description of 1.mp3.\nThis is a second line.\nAnd a third. </itunes:summary>
              <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
              <enclosure url="example.com/tests/media/1.mp3" type="audio/mpeg" length="0"/>
            </item>""",
        ),
        (
            "example.com/",
            "tests/invalid/checksum.md5",
            "Mon, 16 Jan 2017 23:55:07 +0000",
            False,
            """<item>
              <guid>example.com/tests/invalid/checksum.md5</guid>
              <link>example.com/tests/invalid/checksum.md5</link>
              <title>checksum</title>
              <description>checksum</description>
              <itunes:summary>checksum</itunes:summary>
              <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
            </item>""",
        ),
        (
            "example.com/",
            "tests/invalid/windows.exe",
            "Mon, 16 Jan 2017 23:55:07 +0000",
            False,
            """<item>
              <guid>example.com/tests/invalid/windows.exe</guid>
              <link>example.com/tests/invalid/windows.exe</link>
              <title>windows</title>
              <description>windows</description>
              <itunes:summary>windows</itunes:summary>
              <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
            </item>""",
        ),
        (
            "example.com/",
            "tests/media/mp3_with_tags.mp3",
            "Mon, 16 Jan 2017 23:55:07 +0000",
            False,
            """<item>
              <guid>example.com/tests/media/mp3_with_tags.mp3</guid>
              <link>example.com/tests/media/mp3_with_tags.mp3</link>
              <title>mp3_with_tags</title>
              <description>mp3_with_tags</description>
              <itunes:summary>mp3_with_tags</itunes:summary>
              <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
              <enclosure url="example.com/tests/media/mp3_with_tags.mp3" type="audio/mpeg" length="803"/>
              <itunes:duration>0</itunes:duration>
            </item>""",
        ),
        (
            "example.com/",
            "tests/media/mp3_with_tags.mp3",
            "Mon, 16 Jan 2017 23:55:07 +0000",
            True,
            """<item>
              <guid>example.com/tests/media/mp3_with_tags.mp3</guid>
              <link>example.com/tests/media/mp3_with_tags.mp3</link>
              <title>Test media file with ID3 tags</title>
              <description>Test media file with ID3 tags</description>
              <itunes:summary>Test media file with ID3 tags</itunes:summary>
              <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
              <enclosure url="example.com/tests/media/mp3_with_tags.mp3" type="audio/mpeg" length="803"/>
              <itunes:duration>0</itunes:duration>
            </item>""",
        ),
        (
            "example.com/",
            "tests/silence/silence_2.5_seconds.wav",
            "Mon, 16 Jan 2017 23:55:07 +0000",
            True,
            """<item>
              <guid>example.com/tests/silence/silence_2.5_seconds.wav</guid>
              <link>example.com/tests/silence/silence_2.5_seconds.wav</link>
              <title>silence_2.5_seconds</title>
              <description>silence_2.5_seconds</description>
              <itunes:summary>silence_2.5_seconds</itunes:summary>
              <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
              <enclosure url="example.com/tests/silence/silence_2.5_seconds.wav" type="audio/x-wav" length="220544"/>
              <itunes:duration>2</itunes:duration>
            </item>""",
        ),
    ],
    ids=[
        "mp3_no_metadata_description_file",
        "checksum_md5_no_metadata",
        "windows_exe_no_metadata",
        "mp3_with_metadata_false",
        "mp3_with_metadata_true",
        "wav_with_metadata",
    ],
)
def test_file_to_item(host, fname, pub_date, use_metadata, expected_item):
    item = file_to_item(host, fname, pub_date, use_metadata)
    item = re.sub(r"\s+", " ", item.strip())
    expected_item = re.sub(r"\s+", " ", expected_item.strip())
    assert item == expected_item


@pytest.mark.parametrize(
    "dirname, extensions, recursive, followlinks, expected_files",
    [
        (
            os.path.join("tests", "media"),
            None,
            False,
            False,
            [
                os.path.join("tests", "media", f)
                for f in [
                    "1.mp3",
                    "1.mp4",
                    "1.ogg",
                    "2.MP3",
                    "flac_with_tags.flac",
                    "mp3_with_tags.mp3",
                ]
            ],
        ),
        (
            os.path.join("tests", "media"),
            ["mp3"],
            False,
            False,
            [
                os.path.join("tests", "media", f)
                for f in ["1.mp3", "2.MP3", "mp3_with_tags.mp3"]
            ],
        ),
        (
            os.path.join("tests", "media"),
            ["mp4"],
            True,
            False,
            [
                os.path.join("tests", "media", "1.mp4"),
                os.path.join("tests", "media", "subdir_1", "2.MP4"),
                os.path.join("tests", "media", "subdir_2", "4.mp4"),
            ],
        ),
    ],
    ids=[
        "all_files_in_media",
        "only_mp3_files_in_media",
        "recursive_mp4_files_in_media",
    ],
)
def test_get_files(dirname, extensions, recursive, followlinks, expected_files):
    assert get_files(dirname, extensions, recursive, followlinks) == expected_files
