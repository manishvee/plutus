import pandas as pd
from flask import g
from google.cloud import bigquery

from plutus.config import BQ_DATASET, BQ_PROJECT


def get_db_conn():
    if "db" not in g:
        g.db = bigquery.Client()

    return g.db


def load_data(df: pd.DataFrame, table: str):
    job = get_db_conn().load_table_from_dataframe(
        df, f"{BQ_PROJECT}.{BQ_DATASET}.{table}"
    )

    return job.result()


def extract_data(query: str) -> pd.DataFrame:
    query_job = get_db_conn().query(query)
    rows = query_job.result()

    df = rows.to_arrow().to_pandas()
    return df


def execute_query(query: str):
    get_db_conn().query(query)


def close_db_conn(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db_conn)
