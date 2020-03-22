from datetime import datetime
import csv
import io
from typing import Any, Generator
from .BaseConverter import BaseConverter

class AmazonPrimeViewingHistoryConverter (BaseConverter):
    """ Converts an Amazon Prime watch history CSV to a UDIF.

    Overview
    --------

    The Amazon Prime viewing history file is a CSV file. An example is as follows:

    ```text
    Playback Hour,Operating System,Browser,Delivery Type,City,Country,ISP,State,Content Quality Entitled,Entitlement Type,Video Type,Audio Language,Title
    01/13/2016 22:00:00,Roku OS,,streaming,miami,us,HWC,fl,HD,PRIME_SUBSCRIPTION,Feature,,While We're Young
    02/04/2016 01:00:00,Roku OS,,streaming,miami,us,HWC,fl,HD,RENTAL,Feature,,The Perfect Guy
    02/04/2016 21:00:00,Roku OS,,streaming,miami,us,HWC,fl,HD,TRAILER,Trailer,,The Words
    ```

    Converting to UDIF is pretty simple: we insert entries into the activity stream for each line in the CSV. Each entry
    will look like this:

    ```json
    {
        "timestamp": "2020-02-04T01:00:00.000Z",
        "service": "amazon",
        "type": "watch_video",
        "meta": {
            "operating_system": "Roku OS",
            "browser": "",
            "delivery_type": "streaming",
            "isp": "HWC",
            "content_quality_entitled": "HD",
            "entitlement_type": "RENTAL",
            "video_type": "Feature",
            "audio_language": "",
            "video_title": "The Perfect Guy"
        },
        "location": {
            "text": "miami, fl, us",
            "city": "miami",
            "state": "fl",
            "country": "us"
        }
    },
    ```

    Note that the timestamp should be ISO 8601.

    Usage
    -----

    ```python
    with open("Digital.PrimeVideo.Viewinghistory.csv", "r") as input_file:
        with open("output.udif", "a+") as output_file:
            udif_objects = AmazonPrimeViewingHistoryConverter(input_file).parse_to_file(output_file)
    ```
    """

    def __init__(self, input_stream : io.TextIOBase):
        """ Create a new converter with the given input stream. """
        self.input_stream = input_stream
    
    def converter_id(self):
        return "amazon/prime_viewing_history/1.0.0"

    def parse(self, account_id : str = None, *args, **kwargs) -> Generator[Any, None, None]:
        """ Load data from the given input stream into UDIF objects. """
        
        for row in csv.DictReader(self.input_stream):
            yield self.record({
                "udif": { "account_id": account_id },
                "timestamp": datetime.strptime(row["Playback Hour"], "%m/%d/%Y %H:%M:%S").isoformat() + "Z",
                "service": "amazon",
                "type": "watch_video",
                "meta": {
                    "video_title": row["Title"],
                    "operating_system": row["Operating System"],
                    "browser": row["Browser"],
                    "delivery_type": row["Delivery Type"],
                    "isp": row["ISP"],
                    "content_quality_entitled": row["Content Quality Entitled"],
                    "entitlement_type": row["Entitlement Type"],
                    "video_type": row["Video Type"],
                    "audio_language": row["Audio Language"]
                },
                "location": {
                    "text": "{}, {}, {}".format(row["City"], row["State"], row["Country"]),
                    "city": row["City"],
                    "state": row["State"],
                    "country": row["Country"],
                }
            })
