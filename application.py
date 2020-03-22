#!/usr/bin/env python
#
# application.py
# This Flask app contains the routing for our API.

import io
import json
import jsonschema

from datetime import datetime
from flask import Flask, request
from typing import Any, Union, Tuple, List

from data_access.postgres_udif_storage import PostgresUdifStorage
from data_access.models import *
from udif_converters.udif.converters import *
from udif_converters.udif.UdifReader import UdifReader

app = Flask(__name__)
app.config.from_pyfile("configuration.py")
app.config.from_pyfile("configuration.{}.py".format(app.env))

storage = PostgresUdifStorage(app.config["DATABASE_URL"])

@app.route("/update", methods=["POST"])
def update() -> Union[str, Tuple[str, int]]:
    """
    Save a UDIF file to the database, adding to existing information for the user.

    You must provide some __unique__ user ID with the request as the `user` parameter: `?user=<user_id>`.
    
    Overview
    --------

    Content aggregators will call this method to add a UDIF file to our dataset. The UDIF should be passed as the body
    of the request.

    Returns
    -------

    This method will return:

    - `200 OK` upon success, with a JSON result containing the database ID of the UDIF object.
    - `400 Bad Request` if you do not pass the `user` argument, you do not pass a UDIF file, or the UDIF file does not
      match the UDIF schema.
    
    Example Usage
    -------------

    With a file called `data.udif` in the same directory:

    ```bash
    curl --data-binary @data.udif \\
        -H 'Content-Type: text/plain' \\
        -H 'X-API-Key: GZWACJQCVIQNJOCDLDFJTWFWUYYZVCDN' \\
        'http://localhost:5000/update?user=rchowe'
    ```

    """
    
    user = request.args.get("user")
    if not user:
        return bad_request("User argument cannot be none.")
    
    data = request.get_data(as_text=True)
    if not data:
        return bad_request("No data provided with request.")
    
    # Update the UDIF file.
    try:
        udif = update_udif(user, data)
    except UdifValidationError as e:
        return json.dumps({
            "error": "UDIF file did not validate.",
            "validation_errors": [
                {
                    "line": line,
                    "error": "JSON decode error at line {}, col {}".format(error.lineno, error.colno) if isinstance(error, json.decoder.JSONDecodeError) else error.message
                }
                for (line, error) in e.errors]
        }), 400

    return json.dumps({
        "id": udif.id,
        "user_id": udif.user_id
    })

@app.route("/update/<converter>", methods=["POST"])
def update_converter(converter : str) -> Union[str, Tuple[str, int]]:
    """
    Convert a file to UDIF and update the user's file. The parameters are identical to `update`, except you can also
    pass:
    
    1. `service_account_id` for what the service thinks the user's account is.
    2. `timestamp` for when the data was acquired.

    See the `converters` variable below for a list of converters.

    Example Usage
    -------------

    ```bash
    curl --data-binary @NetflixViewingHistory.csv \\
        -H 'Content-Type: text/plain' \\
        -H 'X-API-Key: GZWACJQCVIQNJOCDLDFJTWFWUYYZVCDN' \\
        'http://localhost:5000/update/netflix?user=rchowe'
    ```
    """

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return bad_request("The `X-API-Key` header is not set.")
    if not storage.authenticate(api_key):
        return bad_request("The API key sent was not valid.")
    
    user = request.args.get("user")
    if not user:
        return bad_request("User argument cannot be none.")
    
    data = request.get_data(as_text=True)
    if not data:
        return bad_request("No data provided with request.")

    if converter not in converters:
        return bad_request("Converter '{}' is not supported.".format(converter))

    try:
        udif_data = converters[converter]["constructor"](io.StringIO(data)).parse(
            account_id=request.args.get("service_account_id"),
            timestamp=request.args.get("timestamp") or datetime.utcnow().replace(microsecond=0).isoformat())
        udif = update_udif_raw(user, udif_data)
    except UdifValidationError as e:
        return json.dumps({
            "error": "UDIF file did not validate.",
            "validation_errors": [
                {
                    "line": line,
                    "error": error.message
                }
                for (line, error) in e.errors]
        }), 400
    except Exception as e:
        return json.dumps({
            "error": "UDIF file could not be converted.",
            "exception": str(e)
        })

    return json.dumps({
        "id": udif.id,
        "user_id": udif.user_id
    })
    
def bad_request(message : str) -> (str, int):
    """
    Return a tuple with a JSON error message for use in Flask routes.
    """
    return json.dumps({
        "error": message
    }), 400

def update_udif(user_id : str, data : str) -> Udif:
    """
    Update a UDIF file in the database, or create it if it does not exist.

    :param user_id The user ID to update in the database.
    :param data The string to append to the file in the database.
    :return The `Udif` object from the database.
    """

    reader = UdifReader(io.StringIO(data))
    errors = reader.validate()
    if errors:
        raise UdifValidationError(errors)

    return update_udif_raw(user_id, list(reader))

def update_udif_raw(user_id : str, data : Any) -> Udif:
    """
    Update a UDIF file in the database, or create it if it does not exist.

    :param user_id The user ID to update in the database.
    :param data The UDIF objects to append to the database.
    :return The `Udif` object from the database.
    """

    session = storage.session()
    udif = session.query(Udif).filter_by(user_id=user_id).first()
    
    if udif:
        udif.contents += data
    else:
        udif = Udif(user_id=user_id, contents=data)
        session.add(udif)
    
    session.commit()

    return udif


class UdifValidationError (Exception):
    """
    Thrown by `update_udif` if a file does not validate.
    """

    def __init__(self, errors : List[Tuple[int, jsonschema.ValidationError]]):
        self.errors = errors

converters = {
    "amazon-prime-video": {
        "accepts_folder": False,
        "constructor": AmazonPrimeViewingHistoryConverter
    },
    "google-play-movies-tv": {
        "accepts_folder": False,
        "constructor": GooglePlayMoviesTVHistoryConverter
    },
    "google-play-music": {
        "accepts_folder": True,
        "constructor": GooglePlayMusicConverter
    },
    "netflix": {
        "accepts_folder": False,
        "constructor": NetflixWatchHistoryConverter
    },
    "youtube-history": {
        "accepts_folder": False,
        "constructor": YouTubeHistoryConverter
    },
    "youtube-subscriptions": {
        "accepts_folder": False,
        "constructor": YouTubeSubscriptionsConverter
    },
}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
