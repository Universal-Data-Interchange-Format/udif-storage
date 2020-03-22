import csv
import sys
import uuid
from datetime import datetime
from typing import Any, Generator
from .BaseConverter import BaseConverter

class NetflixWatchHistoryConverter (BaseConverter):
    """ Supports converting a Netflix Viewing History CSV to UDIF.
    
    Overview
    --------

    The Netflix Viewing History file is about the simplest file you can get. It is a CSV file that only has titles and
    dates, with a brief header. Here are the first few lines of mine:

    ```text
    Title,Date
    "The Dark Knight","2/5/20"
    "Great News: Season 1: Pilot","1/20/20"
    "Seth Meyers: Lobby Baby","1/20/20"
    "John Mulaney: New in Town","1/18/20"
    ```

    Usage
    -----

    ```python
    with open("NetflixWatchHistory.csv", "r") as input_file:
        udif_objects = NetflixWatchHistoryConverter(input_file).load()
    with open("output.udif", "w") as output_file:
        udif.writer(output_file).write(udif_objects)
    ```
    """

    input_stream = None

    def __init__(self, input_stream : Any):
        """ Create a new converter with the given input stream. """
        self.input_stream = input_stream
    
    def converter_id(self) -> str:
        """ The converter ID; see `BaseConverter.converter_id()` """
        return "netflix/watch_history/1.0.0"
    
    def parse(self, account_id : str = None, timestamp : str = None, *args, **kwargs) -> Generator[Any, None, None]:
        """ Load data from the given input stream into UDIF objects. """

        reader = csv.DictReader(self.input_stream, *args, **kwargs)

        if not set(reader.fieldnames).issuperset(set(["Title", "Date"])):
            raise NetflixFileFormatException("Columns 'Title' and 'Date' were not both found in CSV.")
        elif set(reader.fieldnames) != set(["Title", "Date"]):
            print("WARNING: Netflix watch history file contains more columns than Title and Date.", file=sys.stderr)

        for row in reader:
            yield self.record({
                "udif": { "account_id": account_id },
                "timestamp": datetime.strptime(row["Date"], "%m/%d/%y").isoformat() + "Z",
                "service": "netflix",
                "type": "watch_video",
                "meta": {
                    "video_title": row["Title"]
                }
            })

class NetflixFileFormatException (Exception):
    """ An exception for when the Netflix Watch History file is not in the format that the NetflixWatchHistoryConverter
        class expects it to be in. """
    pass
