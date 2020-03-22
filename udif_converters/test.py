#!/usr/bin/env python

from datetime import datetime
import udif, udif.converters
import json

start = datetime.utcnow()

with open("data.udif", "a+") as output_file:
    #with open("/Users/rchowe/Downloads/NetflixViewingHistory.csv", "r") as f:
    #    udif.converters.NetflixWatchHistoryConverter(f).parse_to_file(output_file)
    with open("/Users/rchowe/Downloads/Digital.PrimeVideo.Viewinghistory.csv", "r") as f:
        udif.converters.AmazonPrimeViewingHistoryConverter(f).parse_to_file(output_file)
    #with open("/Users/rchowe/Downloads/MyActivity.html", "r") as f:
    #    udif.converters.GooglePlayMoviesTVHistoryConverter(f).parse_to_file(output_file)
    #with open("/Users/rchowe/Downloads/watch-history (YouTube).html", "r") as f:
    #    udif.converters.YouTubeHistoryConverter(f).parse_to_file(output_file)
    #with open("/Users/rchowe/Downloads/subscriptions.json", "r") as f:
    #    udif.converters.YouTubeSubscriptionsConverter(f).parse_to_file(output_file)
    #udif.converters.GooglePlayMusicConverter("/Users/rchowe/Downloads/Google Play Music/").parse_to_file(output_file)

now = datetime.utcnow()
print("Converting took {}".format(now - start))

# Validate that the resultant UDIF file can be read with the built in UdifReader class.
with open("data.udif", "r") as fp:
    reader = udif.reader(fp)
    reader.validate()
    print(reader.data_frame())
