from application import app
from data_access.postgres_udif_storage import PostgresUdifStorage
import json

pg = PostgresUdifStorage(app.config["DATABASE_URL"])
pg.create_all()

raw_json = """
{
    "test": 1
}
"""
pg.save(json.dumps(json.loads(raw_json)))
