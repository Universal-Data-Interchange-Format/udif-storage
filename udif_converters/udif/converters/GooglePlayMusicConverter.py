import csv
import os
import re
import sys
import uuid
from collections import OrderedDict
from datetime import datetime
from html.parser import HTMLParser
from typing import Any, Generator, List
from .BaseConverter import BaseConverter

class GooglePlayMusicConverter (BaseConverter):
    """ Converts a Google Play Music personal information file to UDIF.

    Overview
    --------

    Google Play Music provides information as CSV files in a folder directory structure. Broadly, the folder structure
    looks like this:

    ```text
    |- Playlists
       |- Playlist #1
          |- Metadata.csv
          |- Tracks
             |- Track #1 Name.csv
             |- Track #2 Name.csv
             |- ...
          |- Tracks.csv
       |- Playlist #2
       |- ...
    |- Radio Stations
       |- My Stations
          |- Station #1 Name.csv
          |- Station #2 Name.csv
          |- ...
       |- Recent Stations
          |- Station #1 Name.csv
          |- Station #2 Name.csv
          |- ...
    |- Tracks
       |- Name #1.csv
       |- Name #2.csv
    ```

    ### Timestamps

    Unfortunately, timestamps are not given in any of these files. Due to this, we provide two solutions:

    1. The user can provide a timestamp as an argument to the `GooglePlayMusicConverter()` constructor, which will be
       included with the generated entries.
    2. The generated JSON includes a `uid` field with a unique ID number and a `generated_timestamp` field with the
       timestamp at which the information was parsed. The `uid` will match across all entries generated at the same
       time.
    
    Note that simply providing the time of parsing as the timestamp is not recommended unless it is known that the time
    at which the file is being provided matches the time at which the file was requested, due to the likelihood of
    providing bad data.

    ### Generated Entries

    For each playlist in the dataset, an entry of the following format is generated:

    ```json
    {
        "timestamp": "2020-02-04T01:00:00.000Z",
        "uid": "e8e16dba-619d-46b5-832e-1f08529502e3",
        "generated_timestamp": "2020-02-04T01:00:00.000Z",
        "account_id": "e8e16dba-619d-46b5-832e-1f08529502e3",
        "service": "google_play_music",
        "type": "playlist",
        "meta": {
            "playlist_name": "Playlist #1",
            "tracks": [
                {
                    "title": "Add Me In",
                    "album": "X (Deluxe Version)",
                    "artist": "Chris Brown",
                    "duration_ms": 193121,
                    "rating": 0,
                    "play_count": 0,
                    "removed": ""
                }
            ]
        }
    },
    ```

    For each radio station in the dataset, an entry of the following format is generated:

    ```json
    {
        "timestamp": "2020-02-04T01:00:00.000Z",
        "uid": "e8e16dba-619d-46b5-832e-1f08529502e3",
        "generated_timestamp": "2020-02-04T01:00:00.000Z",
        "account_id": "e8e16dba-619d-46b5-832e-1f08529502e3",
        "service": "google_play_music",
        "type": "radio_station",
        "meta": {
            "radio_station_type": "My Stations",
            "radio_station_title": "Cardio Hip Hop",
            "radio_station_artist": "By Google Play Music",
            "radio_station_description": "This collection of heart-thumping hip hop beats will help you reach the next level in yoru cardio workouts.",
            "radio_station_removed": null,
            "radio_station_artists_played": [
                "Drake",
                "Tyga"
            ],
            "radio_station_similar_stations": [
                "Three Wheel Motion",
                "School Spirit: HBCU Edition"
            ]
        }
    },
    ```

    A single entry of the following format, for all of the tracks in the user's library is generated.

    ```json
    {
        "timestamp": "2020-02-04T01:00:00.000Z",
        "uid": "e8e16dba-619d-46b5-832e-1f08529502e3",
        "generated_timestamp": "2020-02-04T01:00:00.000Z",
        "account_id": "e8e16dba-619d-46b5-832e-1f08529502e3",
        "service": "google_play_music",
        "type": "library",
        "meta": {
            "tracks": [
                ...
            ]
        }
    },
    ```

    Note that the timestamp should be ISO 8601.

    Usage
    -----

    If you know that the file is fresh and want to provide the current time as a timestamp:

    ```python
    udif_objects = GooglePlayMusicConverter("/path/to/GooglePlayMusicFolder", timestamp=datetime.now()).load()
    with open("output.udif", "w") as output_file:
        udif.writer(output_file).write(udif_objects)
    ```
    """

    excluded_files = ['.DS_Store']
    
    def __init__(self, directory_path : str):
        """ Set up a new GooglePlayMusicConverter with the given parameters.

        :param directory_path The path to the Google Play Music directory to load. """

        self.directory_path = directory_path
    
    def parse(self, account_id : str = None, timestamp : datetime = None) -> Generator[Any, None, None]:
        """ Load the content of the directory into a given UDIF file.
        
        :param udif_object An existing UDIF object to load data into.
        :param timestamp The timestamp to apply to each item.
        """

        timestamp = timestamp.isoformat() + "Z" if timestamp else None
        
        try:
            subdirectories = self.listdir(self.directory_path)
            if set(subdirectories) - set(["Playlists", "Radio Stations", "Tracks"]):
                print("WARNING: Additional unknown subdirectories found in Google Play Music data folder.")
        except FileNotFoundError:
            print("ERROR: FileNotFoundError when listing directory_path given to GooglePlayMusicConverter.", file=sys.stderr)
            raise
            
        try:
            for playlist in self.load_playlists(os.path.join(self.directory_path, "Playlists"), account_id=account_id):
                yield self.record(playlist)
        except FileNotFoundError:
            print("WARNING: Subdirectory 'Playlists' not found in Google Play Music data folder.")
        
        try:
            for radio_station in self.load_radio_stations(os.path.join(self.directory_path, "Radio Stations"), account_id=account_id):
                yield self.record(radio_station)
        except FileNotFoundError:
            print("WARNING: Subdirectory 'Radio Stations' not found in Google Play Music data folder.")
        
        try:
            yield self.record(self.load_tracks(os.path.join(self.directory_path, "Tracks"), account_id=account_id))
        except FileNotFoundError:
            print("WARNING: Subdirectory 'Tracks' not found in Google Play Music data folder.")
    
    def load_playlists(self, playlists_path : str, account_id : str = None, timestamp : str = None) -> Generator[Any, None, None]:
        """ Load playlist information out of the given path.
        
        :param playlists_path The path to the Playlists folder."""

        for playlist in self.listdir(playlists_path):
            metadata = {}
            track_information = {}
            tracks = []
            
            if playlist != "Thumbs Up":
                try:
                    with open(os.path.join(playlists_path, playlist, "Metadata.csv"), "r") as f:
                        raw_metadata = next(csv.DictReader(f))
                        metadata = {
                            "playlist_title": raw_metadata["Title"],
                            "playlist_owner": raw_metadata["Owner"],
                            "playlist_description": raw_metadata["Description"],
                            "playlist_shared": raw_metadata["Shared"],
                            "playlist_deleted": raw_metadata["Deleted"],
                        }
                except (FileNotFoundError, NotADirectoryError, StopIteration):
                    print("WARNING: Unable to read Metadata.csv file for playlist {0}".format(playlist))

                try:
                    with open(os.path.join(playlists_path, playlist, "Tracks.csv"), "r") as f:
                        raw_tracks = next(csv.DictReader(f))
                        track_information = {
                            "title": raw_tracks.get("Title"),
                            "album": raw_tracks.get("Album"),
                            "artist": raw_tracks.get("Artist"),
                            "duration_ms": raw_tracks.get("Duration (ms)"),
                            "rating": raw_tracks.get("Rating"),
                            "play_count": raw_tracks.get("Play Count"),
                            "removed": raw_tracks.get("Removed"),
                            "playlist_index": raw_tracks.get("Playlist Index"),
                        }
                except (FileNotFoundError, NotADirectoryError, StopIteration):
                    print("WARNING: Unable to read Tracks.csv file for playlist {0}".format(playlist))
            
            try:
                if playlist == "Thumbs Up":
                    tracks_directory = os.path.join(playlists_path, playlist)
                else:
                    tracks_directory = os.path.join(playlists_path, playlist, "Tracks")
                for track in self.listdir(tracks_directory):
                    try:
                        with open(os.path.join(tracks_directory, track)) as f:
                            track = next(csv.DictReader(f))
                            tracks.append({
                                "title": track.get("Title"),
                                "album": track.get("Album"),
                                "artist": track.get("Artist"),
                                "duration_ms": track.get("Duration (ms)"),
                                "rating": track.get("Rating"),
                                "play_count": track.get("Play Count"),
                                "removed": track.get("Removed")
                            })
                    except (FileNotFoundError, NotADirectoryError, StopIteration):
                        print("WARNING: Unable to read found track file {0} in playlist {1}".format(track, playlist))
            except (FileNotFoundError, NotADirectoryError):
                print("WARNING: Unable to read Tracks directory in playlist {0}".format(playlist))
            
            yield {
                "udif": { "account_id": account_id },
                "timestamp": timestamp,
                "account_id": account_id,
                "service": "google_play_music",
                "type": "playlist",
                "meta": {
                    "playlist_title": metadata.get("playlist_title"),
                    "playlist_owner": metadata.get("playlist_owner"),
                    "playlist_description": metadata.get("playlist_description"),
                    "playlist_shared": metadata.get("playlist_shared"),
                    "playlist_deleted": metadata.get("playlist_deleted"),
                    "track_information": track_information,
                    "tracks": tracks
                }
            }

    def load_radio_stations(self, radio_stations_path : str, account_id : str = None, timestamp : str = None) -> Generator[Any, None, None]:
        """ Load playlist information out of the given path.
        
        :param radio_stations_path The path to the Playlists folder."""

        for folder in ["My Stations", "Recent Stations"]:
            try:
                for station in self.listdir(os.path.join(radio_stations_path, folder)):
                    try:
                        with open(os.path.join(radio_stations_path, folder, station), "r") as f:
                            station = next(csv.DictReader(f))
                            yield {
                                "timestamp": timestamp,
                                "account_id": account_id,
                                "service": "google_play_music",
                                "type": "radio_station",
                                "meta": {
                                    "radio_station_type": folder,
                                    "radio_station_title": station.get("Title"),
                                    "radio_station_artist": station.get("Artist"),
                                    "radio_station_description": station.get("Description"),
                                    "radio_station_removed": station.get("Removed"),
                                    "radio_station_artists_played": [x.strip() for x in station.get("Artists on this station", "").split(",") if x],
                                    "radio_station_similar_stations": [x.strip() for x in station.get("Similar Stations", "") if x]
                                }
                            }
                    except (FileNotFoundError, StopIteration):
                        print("WARNING: Unable to read radio station file {0}/{1}".format(folder, station))
            except (FileNotFoundError, NotADirectoryError):
                print("WARNING: Unable to read radio station folder {0}.".format(folder))
                pass

    def load_tracks(self, tracks_path : str, account_id : str = None, timestamp : str = None) -> Generator[Any, None, None]:
        """ Load playlist information out of the given path.
        
        :param tracks_path The path to the Playlists folder."""

        tracks = []
        try:
            for track in self.listdir(tracks_path):
                try:
                    with open(os.path.join(tracks_path, track), "r") as f:
                        track = next(csv.DictReader(f))
                        tracks.append(
                        {
                            "title": track.get("Title"),
                            "album": track.get("Album"),
                            "artist": track.get("Artist"),
                            "duration_ms": track.get("Duration (ms)"),
                            "rating": track.get("Rating"),
                            "play_count": track.get("Play Count"),
                            "removed": track.get("Removed")
                        })
                except (FileNotFoundError, StopIteration):
                    print("WARNING: Unable to read track '{0}'".format(track))
        except (FileNotFoundError, NotADirectoryError):
            print("WARNING: Unable to enumerate tracks folder.")
        
        return {
            "udif": { "account_id": account_id },
            "timestamp": timestamp,
            "account_id": account_id,
            "service": "google_play_music",
            "type": "library",
            "meta": {
                "tracks": tracks
            }
        }
    
    def listdir(self, directory : str) -> List[str]:
        """ List the contents of the directory, less any excluded files. """
        excluded_set = set(self.excluded_files)
        return [f for f in os.listdir(directory) if f not in excluded_set]