import io
import itertools
import json
import jsonschema
import pandas as pd
import dateutil.parser
from collections import OrderedDict
from typing import Any, List, Tuple, Union
from . import schema

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources

class UdifReader:
    """ A unified event file reader of everything from someone's social media history.
    
    Overview
    --------

    This file type is a timeline of events in a user's watching or shopping history, from multiple providers, e.g.
    Facebook, Netflix, etc.. Additional data from the input files can also be stored.

    This is a newline-delimited JSON (ndjson) based file format, so we also provide an option to validate the JSON.

    Example
    -------

    To print all events in a file, do the following:

    ```python
    with open("/path/to/file.udif", "r") as f:
        for event in udif.reader(f):
            print(event.service, event.activity_type, event.timestamp)
    ```

    """

    DEFAULT_SCHEMA = "udif.schema.json"

    def __init__(self,
            stream : io.TextIOBase,
            schema_stream : io.TextIOBase = None,
            autovalidate : bool = True,
            ignore_invalid_lines : bool = False):
        """ Initialize a new EventFile with the given file path.

        This just sets up the reader, the file is not opened until `__enter__` is called, e.g. when used with the `with`
        keyword, or upon the first use of a read function.

        :param stream The input stream of UDIF to read.
        :param schema_stream The input stream of the schema file.
        :param autovalidate Whether to automatically validate a file when opening it.
        :param skip_invalid Whether to, instead of raising a ValidationError, simply ignore invalid lines.
        
        """

        self.stream = stream
        self.autovalidate = autovalidate
        self.ignore_invalid_lines = ignore_invalid_lines
        self.schema = None

        self.load_schema(schema_stream)
    
    def __iter__(self):
        """ Return an iterator of the activity in the timeline, if available.

        Example
        -------

        The best way to use this is in a `for` loop:

        ```python
        with open("file.udif", "r") as f:
            for event in udif.reader(f):
                print(event)
        ```

        However, if you want to load all of the events in a file (not recommended, it has the potential to be quite
        slow), you can also make use of the fact that the reader is an iterator:

        ```python
        with open("file.udif", "r") as f:
            events = list(udif.reader(f))
        ```

        Note that if you wish to use the iterator more than once, you will likely have to `.seek()` the underlying file
        stream passed in the constructor back.

        """

        for line in self.stream:
            event = json.loads(line)

            if self.autovalidate:
                if not self.schema:
                    raise Exception("UdifReader set to autovalidate but no schema is present")
                try:
                    jsonschema.validate(event, self.schema)
                except jsonschema.ValidationError:
                    if not self.ignore_invalid_lines:
                        raise

            yield event

    def validate(self, seek : bool = True) -> List[Tuple[int, Union[jsonschema.ValidationError, json.decoder.JSONDecodeError]]]:
        """ Loop through the file and validate each line of UDIF, returning a list of tuples of
        `(line_number, validation_error)`.

        :param seek Whether to not `.seek()` back in the stream to the position the stream was at before this method
                    was called. This is important for certain streams which do not support `.seek()`, or to save some
                    compute cycles if you only want to validate the file and not read each line.
        
        Example
        -------

        The following might be used to validate a UDIF file than doing something with the data:

        ```python
        with open("data.udif", "r") as fp:
            reader = udif.reader(fp)
            try:
                reader.validate()
            except udif.FileValidationError as validation:
                for error in validation:
                    print(error)
                raise
            
            # Do something once we know the file is valid.
            df = reader.data_frame()
        ```
        """

        if seek:
            if not self.stream.seekable():
                raise ValueError("UdifReader.validate(seek = True) called, but the stream is not seekable!")
            position = self.stream.tell()
        
        try:
            errors = []
            for number, line in enumerate(self.stream, start=1):
                try:
                    event = json.loads(line)
                    jsonschema.validate(event, self.schema)
                except jsonschema.ValidationError as error:
                    errors.append((number, error))
                except json.decoder.JSONDecodeError as error:
                    errors.append((number, error))
        finally:
            if seek:
                self.stream.seek(position)
        
        return errors

    def load_schema(self, stream : io.TextIOBase = None) -> None:
        """ Load the schema to validate against from a given input stream.

        This method is normally called by the constructor; a program will not need to call it unless a different schema
        is required.
        
        :param stream The stream to load the schema from. If this parameter is not provided, the default schema will be
                      used.
        """

        self.schema = json.load(stream or pkg_resources.open_text(schema, self.DEFAULT_SCHEMA))
    
    def data_frame(self, include_raw : bool = False):
        """ Return a pd.DataFrame of the activity in the timeline.
        
        Note that this is only *guaranteed* to have the fields `timestamp`, `service`, `type`, and `location`. Any other
        fields are not guaranteed to be present.

        """

        # The columns to appear first.
        first_columns = ['timestamp', 'service', 'type', 'location']

        df = pd.DataFrame(data=list(self))

        # Fix the timestamps and location.
        if "timestamp" in df:
            df['timestamp'] = [(dateutil.parser.isoparse(t) if t else None) for t in df['timestamp']] 
        if "location" in df:
            df['location'] = [_location_to_text(loc) for loc in df['location']]

        _flatten_content(df)

        if "udif.session_timestamp" in df:
            df['udif.session_timestamp'] = [(dateutil.parser.isoparse(t) if t else None) for t in df['udif.session_timestamp']] 

        # Reindex the data frame so certain columns are always first.
        keys = set(first_columns).union(df.columns)
        if not include_raw:
            keys.discard("raw")
        return df.reindex(columns=first_columns + list(sorted(keys - set(first_columns + ["meta"]))))

def _location_to_text(location : dict) -> str:
    """ Convert the location object into text, either using the display text or the longitude and latitude. """

    if location is None or not isinstance(location, dict):
        return None
    if 'text' in location:
        return location['text']
    if 'longitude' in location and 'longitude' in location:
        return "{0:+f}, {1:+f}".format(location['latitude'], location['longitude'])

def _flatten_content(df : pd.DataFrame, prefixes : List[str] = ["meta", "udif"]) -> None:
    """ Extract the keys from the content object. """

    for prefix in prefixes:
        keys = set(item for sublist in (c.keys() for c in df[prefix] if c) for item in sublist)
        for key in keys:
            df["{prefix}.{key}".format(prefix=prefix, key=key)] = [c.get(key, None) if c else None for c in df[prefix]]
