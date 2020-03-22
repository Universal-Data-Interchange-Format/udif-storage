from datetime import datetime
import io
import json
import uuid
from typing import Any, List, Union, Tuple, Generator

class BaseConverter:
    """ A base class for all converters from arbitrary data formats to UDIF.

    Overview
    --------

    At minimum, converters need to support converting from a file open for reading to a Python representation of the
    UDIF data that conforms to `schema/udif.schema.json`. This is accomplished by overriding the `load` method.

    Converters also should declare some additional information about themselves to allow themselves to be loaded
    dynamically. This is especially true if it is possible to quickly detect a filetype, as this will allow the user to
    not have to tell us what type of file they are uploading.

    Example Usage
    -------------

    This class is designed to be subclassed. Subclasses must override the `load` method with a method that loads new
    rows of UDIF in a given format. For example usage, see the `NetflixWatchHistoryConverter` subclass.
    """

    session_id = None
    session_timestamp = None
    
    def parse(self, *args, **kwargs) -> Generator[Any, None, None]:
        """ Load the file a given array of UDIF objects. Each item in the array must conform to the
        udif_entry.schema.json schema.

        NOTE: This method must be overridden in every subclass.
        """

        raise NotImplementedError()

    def parse_to_file(self, output_stream : io.TextIOBase) -> int:
        """ Load UDIF entries from a given file, then write (append) them to a given UDIF file.
        
        :param output_stream An IO stream to output to.
        :return The number of entries processed.

        TODO: Validate the entries returned from `.parse(str)`.
        """

        for entry in self.parse():
            json.dump(entry, output_stream)
            output_stream.write("\n")
    
    def record(self, modifications : dict = {}):
        """ Return an empty base UDIF record with the given modifications.
        
        This method is meant to be used by subclasses to remove the boilerplate record generation code from each
        subclass. Before using this, a subclass should override the `converter_id()` method.

        """

        session_id, session_timestamp = self.session() or (None, None)

        o = {
            "udif": {
                "converter_id": self.converter_id(),
                "session_id": session_id,
                "session_timestamp": session_timestamp.isoformat() + "Z"
            },

            "timestamp": None,
            "service": None,
            "type": None
        }
        BaseConverter.merge(o, modifications)
        return o
    
    def converter_id(self) -> Union[str, None]:
        """ Returns a string of the converter ID to be included in the UDIF record.
        
        The converter ID should be a string of the format `{service}/{file_type}/{converter_version}`, e.g.

        ```text
        netflix/watch_history/1.0.0
        ```

        """
        return None
    
    def session(self) -> Union[Tuple[str, datetime], None]:
        """ Returns a tuple of the session ID and session timestamp to be included in the UDIF record. If none currently
        exist, they are generated.

        If these need to be overriden in a subclass, set `self.session_id` and `self.session_timestamp` in the
        constructor.
        """

        self.session_id = self.session_id or str(uuid.uuid4())
        self.session_timestamp = self.session_timestamp or datetime.utcnow()

        return (self.session_id, self.session_timestamp)
    
    @classmethod
    def merge(cls, destination : dict, source : dict, path : List[Any] = None) -> None:
        """ Update dict `destination` with the contents of dict `source`, recursively merging dicts if necessary. All
            other elements with the same key will be overwritten with values from `source`.
        
        :param `destination` The dictionary to update.
        :param `source` The dictionary with the keys to add to `destination`.
        :return A reference to `destination`.
        """

        if path is None:
            path = []
        
        for key in source:
            if key in destination and isinstance(destination[key], dict) and isinstance(source[key], dict):
                BaseConverter.merge(destination[key], source[key], path + [str(key)])
            else:
                destination[key] = source[key]
        
        return destination