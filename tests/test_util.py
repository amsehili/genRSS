import os
import re
import pytest
from generss.util import (
    get_title,
    get_duration,
    file_to_item,
    get_files,
)


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
              <description>1</description>
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
              <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
              <enclosure url="example.com/tests/silence/silence_2.5_seconds.wav" type="audio/x-wav" length="220544"/>
              <itunes:duration>2</itunes:duration>
            </item>""",
        ),
    ],
    ids=[
        "mp3_no_metadata",
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
