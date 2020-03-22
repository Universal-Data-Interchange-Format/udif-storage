import csv
import json
import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Any, Generator
from .BaseConverter import BaseConverter

class YouTubeSubscriptionsConverter (BaseConverter):
    """ Converts a Youtube subscriptions JSON file to a UDIF.

    Overview
    --------

    The YouTube viewing history file is an HTML file with the data in tags at the bottom. An example is as follows:

    ```html
    <div class="outer-cell mdl-cell mdl-cell--12-col mdl-shadow--2dp">
      <div class="mdl-grid">
        <div class="header-cell mdl-cell mdl-cell--12-col">
          <p class="mdl-typography--title">YouTube<br></p>
        </div>
        <div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1">Watched Kung Fu Panda 3<br>Jul 13,
          2016, 2:17:59 PM EDT</div>
        <div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1 mdl-typography--text-right"></div>
        <div class="content-cell mdl-cell mdl-cell--12-col mdl-typography--caption"><b>Products:</b><br>&emsp;YouTube<br></div>
      </div>
    </div>
    ```

    Converting to UDIF involves using Python's built-in HTML parser 

    ```json
    {
        "timestamp": "2020-02-04T01:00:00.000Z",
        "service": "youtube",
        "type": "watch_video",
        "meta": {
            "video_title": "Kung Fu Panda 3"
        }
    },
    ```

    Note that the timestamp should be ISO 8601.

    Usage
    -----

    ```python
    with open("subscriptions.json", "r") as input_file:
        udif_objects = YouTubeSubscriptionsConverter(input_file).load()
    with open("output.udif", "w") as output_file:
        udif.writer(output_file).write(udif_objects)
    ```
    """

    def __init__(self, input_stream : Any):
        """ Create a new converter with the given input stream. """
        self.input_stream = input_stream
    
    def parse(self, account_id : str = None, timestamp : str = None, *args, **kwargs) -> Generator[Any, None, None]:
        """ Load data from the given input stream into UDIF objects. """

        for subscription in json.load(self.input_stream):
            snippet = subscription.get("snippet", {})

            yield self.record({
                "udif": {
                    "account_id": account_id
                },
                "timestamp": snippet.get("publishedAt"),
                "service": "youtube",
                "type": "channel_subscription",
                "meta": {
                    "channel_name": snippet.get("title"),
                    "channel_description": snippet.get("description"),
                    "youtube_subscription_id": subscription.get("id"),
                    "youtube_channel_id": snippet.get("channel_id")
                },
                "raw": subscription
            })
    
    def converter_id(self) -> str:
        return "youtube/subscriptions/1.0.0"