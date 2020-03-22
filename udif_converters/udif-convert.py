#!/usr/bin/env python
"""
udif-convert.py
A command-line tool to use UDIF parsers.

Usage
-----

The program is called from the command line as follows:

    ./udif-convert.py <converter> <file1> [<file2> [...]] [-a account_id] [-c converter] [-o output_file]

Run `./udif-convert.py --help` to see the argparse help which may be more useful.

For some converters (currently only Google Play Music), a directory path is used instead of a file path.

"""

import argparse
import json
import sys
from udif.converters import *

converters = {
    "amazon-prime-video": {
        "accepts_folder": False,
        "binary": False,
        "constructor": AmazonPrimeViewingHistoryConverter
    },
    "google-play-movies-tv": {
        "accepts_folder": False,
        "binary": False,
        "constructor": GooglePlayMoviesTVHistoryConverter
    },
    "google-play-music": {
        "accepts_folder": True,
        "binary": False,
        "constructor": GooglePlayMusicConverter
    },
    "netflix-watch-history": {
        "accepts_folder": False,
        "binary": False,
        "constructor": NetflixWatchHistoryConverter
    },
    "youtube-history": {
        "accepts_folder": False,
        "binary": False,
        "constructor": YouTubeHistoryConverter
    },
    "youtube-subscriptions": {
        "accepts_folder": False,
        "binary": False,
        "constructor": YouTubeSubscriptionsConverter
    },
}

def main():
    parser = argparse.ArgumentParser(description="A command-line tool to use UDIF parsers.")
    parser.add_argument("converter", metavar="converter", nargs=1, choices=converters.keys(),
        help="Specify the converter to use by name. Available converters are: " + ", ".join(converters.keys()))
    parser.add_argument('files', metavar='input_file', type=str, nargs='+',
        help="Input files to convert to UDIF. Note that all files must be of the same type (e.g. all Netflix). If the "
            + "only input file is '-', then stdin is used as input.")
    parser.add_argument("-a", "--account", dest="account", metavar="account_id", nargs=1,
        help="Specify an account ID to pass to the converter.")
    parser.add_argument("-o", "--output", dest="output", metavar="output_file",
        nargs=1, help="The file to write the output to. If not specified, output is written to stdout.")
    parser.add_argument("-t", "--timestamp", dest="timestamp", metavar="timestamp",
        nargs=1, help="The timestamp to apply to entries without a timestamp.")

    args = parser.parse_args()

    converter = converters[args.converter[0]]
    if not converter:
        raise Exception("Invalid converter")
    
    if not args.output or args.output[0] == "-":
        for filename in args.files:
            for line in get_generator(converter, args, filename):
                print(json.dumps(line))
    else:
        with open(args.output[0], "w") as outfile:
            for filename in args.files:
                for line in get_generator(converter, args, filename):
                    print(json.dumps(line), file=outfile)


def get_generator(converter, args, filename):
    """ Wrap the logic of which file to use in a function and generator so that we can use the `with` statement without
        too much repetition. """
    
    if converter["accepts_folder"]:
        return converter["constructor"](filename).parse(
            account_id=args.account,
            timestamp=args.timestamp)
    else:
        if converter["binary"]:
            if filename == "-":
                return converter["constructor"](sys.stdin).parse(
                    account_id=args.account,
                    timestamp=args.timestamp)
            else:
                with open(filename, "rb") as f:
                    for line in converter["constructor"](f).parse(
                            account_id=args.account,
                            timestamp=args.timestamp):
                        yield line
        
        else:
            if filename == "-":
                return converter["constructor"](sys.stdin).parse(
                    account_id=args.account,
                    timestamp=args.timestamp)
            else:
                with open(filename, "r") as f:
                    for line in converter["constructor"](f).parse(
                            account_id=args.account,
                            timestamp=args.timestamp):
                        yield line

if __name__ == "__main__":
    main()
