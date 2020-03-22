import csv
import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Any
from .BaseConverter import BaseConverter

class GooglePlayMoviesTVHistoryConverter (BaseConverter):
    """ Converts an Google Play watch history HTML file to a UDIF.

    Overview
    --------

    The Google Play Movies & TV viewing history file is an HTML file with the data in tags at the bottom. An example is
    as follows:

    ```html
    <div class="outer-cell mdl-cell mdl-cell--12-col mdl-shadow--2dp">
      <div class="mdl-grid">
        <div class="header-cell mdl-cell mdl-cell--12-col">
          <p class="mdl-typography--title">Google Play Movies &amp; TV<br></p>
        </div>
        <div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1">Watched Kung Fu Panda 3<br>Jul 13,
          2016, 2:17:59 PM EDT</div>
        <div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1 mdl-typography--text-right"></div>
        <div class="content-cell mdl-cell mdl-cell--12-col mdl-typography--caption"><b>Products:</b><br>&emsp;Google
          Play Movies &amp; TV<br></div>
      </div>
    </div>
    ```

    Converting to UDIF involves using Python's built-in HTML parser 

    ```json
    {
        "timestamp": "2020-02-04T01:00:00.000Z",
        "service": "google_play_movies_tv",
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
    with open("MyActivity.html", "r") as input_file:
        udif_objects = GooglePlayMoviesTVHistoryConverter(input_file).load()
    with open("output.udif", "w") as output_file:
        udif.writer(output_file).write(udif_objects)
    ```
    """

    input_stream = None

    def __init__(self, input_stream : Any):
        """ Create a new converter with the given input stream. """
        self.input_stream = input_stream
    
    def converter_id(self):
        return "google/play_movies_tv/1.0.0"

    def parse(self, *args, **kwargs) -> Any:
        """ Load data from the given input stream into UDIF objects. """
        
        parser = GooglePlayHTMLParser()
        parser.feed(self.input_stream.read())
        return (self.record(event) for event in parser.events(*args, **kwargs))


class GooglePlayHTMLParser (HTMLParser):
    """ A very simple HTML parser for extracting data from the Google Play Movies and TV history file.
    
    Basically, this works based on the fact that there are only five formats of text in the file:

    - Google Play Movies & TV
    - Products:
    - Used [APP_NAME]
    - Watched [VIDEO_NAME]
    - Jun 4, 2017, 9:59:36 PM EDT

    Given that the date always comes after the activity, we filter out the first two types of text and keep the
    Used/Watched lines and the date immediately after.
    """

    IGNORED_DATA = set([
        "google play movies & tv",
        "products:"
    ])

    process_data = False

    lines = []

    def handle_starttag(self, tag, attrs):
        """ Don't start handling data until the body comes up. """
        if tag == "body":
            self.process_data = True

    def handle_data(self, data):
        """ When we come up with some data, apply the rules in the top level docstring. """

        if not self.process_data:
            return

        data = re.sub(r"\s+", " ", ''.join([c for c in data if ord(c) > 31 or ord(c) == 9])).strip()
        if data.lower() in self.IGNORED_DATA or not data:
            return
        
        self.lines.append(data)
    
    def events(self, account_id : str = None, *args, **kwargs):
        event_action = None
        event_name = None

        for line in self.lines:
            if re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2}, \d{4}", line):
                event_date = datetime.strptime(line, "%b %d, %Y, %H:%M:%S %p %Z").isoformat() + "Z"

                if event_action == "use_app":
                    meta = { "app_name": event_name }
                elif event_action == "watch_video":
                    meta = { "video_title": event_name }
                else:
                    meta = {}
                
                yield {
                    "udif": { "account_id": account_id },
                    "timestamp": event_date,
                    "service": "google_play_movies_tv",
                    "type": event_action or "unknown",
                    "meta": meta
                }

                event_action = None
                event_name = None
                
            elif re.match(r"^Used ", line):
                event_action = "use_app"
                event_name = line[5:]

            elif re.match(r"Watched ", line):
                event_action = "watch_video"
                event_name = line[8:]
            
            else:
                print("Unknown line detected in google play file:\n  " + line)
