import argparse
import subprocess
import os
from ilias import IliasClient
from time import sleep
from threading import Thread
import re

# read url from command line
# or read url list file from command line
parser = argparse.ArgumentParser(description="Downloads ILIAS Streams")
parser.add_argument("--url", help="URL of the ILIAS Stream")
parser.add_argument("--overview-url", help="URL of the ILIAS video overview")
parser.add_argument(
    "--cookie",
    help="Cookie header for ILIAS authentication. Required if --overview-url is set.",
)
parser.add_argument("--output-file", help="Output file")
parser.add_argument("--url-list-path", help="URL list of the ILIAS Streams")

args = parser.parse_args()


def convert_title_to_filename(title: str):
    replace_dict = {
        " ": "_",
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
        ".": "_",
        "\n:": "",
        ":": "_",
        ",": "_",
        ";": "_",
    }
    title = title.lower().strip()
    for key, value in replace_dict.items():
        title = title.replace(key, value)
    return title + ".mkv"


def get_url_filename_tuple_list():
    url_filename_tuple_list = []
    if args.url:
        url_filename_tuple_list.append((args.url, args.output_file))
    if args.url_list_path:
        with open(args.url_list_path) as f:
            for line in f:
                url, output_file = line.split()
                url_filename_tuple_list.append((url, output_file))
            print(
                f"Found {len(url_filename_tuple_list)} streams in {args.url_list_path}"
            )

    if args.overview_url:
        iliasClient = IliasClient(args.cookie)
        overview_url = iliasClient.get_video_overview_url(args.overview_url)
        videos_data = iliasClient.get_videos_data(overview_url)

        print(f"Found {len(videos_data)} streams in {args.overview_url}")

        def set_stream_url(stream_dict, key, video_link):
            stream_dict[key] = iliasClient.get_stream_link(video_link)

        stream_dict = {}
        threads = []
        for i, video_data in enumerate(videos_data):
            threads.append(
                Thread(
                    target=set_stream_url,
                    args=(stream_dict, i, video_data["link"]),
                )
            )
            threads[i].start()

        for i, video_data in enumerate(videos_data):
            threads[i].join()
            print(f"Waiting for stream urls: {i+1}/{len(videos_data)}", end="\r")

            stream_url = stream_dict[i]
            filename = convert_title_to_filename(video_data["title"])
            url_filename_tuple_list.append((stream_url, filename))
        print("Fetched all stream urls")

    return url_filename_tuple_list


def download_and_convert(url, output_file):
    print(f"Downloading...", end="\r")
    devnull = open(os.devnull, "w")
    tmp_file_path = "/tmp/ilias_stream.mp4"

    # remove old tmp file if exists
    if os.path.exists(tmp_file_path):
        os.remove(tmp_file_path)

    # call hlsdl with url
    subprocess.call(
        ["hlsdl", "-b", "-o", tmp_file_path, url],
        stdout=devnull,
        stderr=devnull,
    )

    print(f"Converting...", end="\r")
    # convert to mkv with ffmpeg
    subprocess.call(
        ["ffmpeg", "-i", tmp_file_path, "-c", "copy", output_file],
        stdout=devnull,
        stderr=devnull,
    )

    # remove tmp file
    os.remove(tmp_file_path)


if __name__ == "__main__":
    print("Starting Apollo - ILIAS Stream Downloader")
    url_filename_tuple_list = get_url_filename_tuple_list()

    print(f"Found {len(url_filename_tuple_list)} streams to download")
    i = 1
    for url, output_file in url_filename_tuple_list:
        download_and_convert(url, output_file)
        print(f"Finished {i}/{len(url_filename_tuple_list)}")
        i += 1

    print("Finished downloading all streams")
