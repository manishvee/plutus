import io
from dataclasses import dataclass

import pandas as pd
import polars as pl
from google.cloud import bigquery


@dataclass
class BigQueryConnector:
    project: str
    dataset: str

    def __post_init__(self):
        self.client = bigquery.Client()

    def load(self, df: pd.DataFrame, table: str):
        job = self.client.load_table_from_dataframe(df, f"{self.project}.{self.dataset}.{table}")

        return job.result()

    def extract(self, query: str) -> pd.DataFrame:
        query_job = self.client.query(query)
        rows = query_job.result()

        df = rows.to_arrow().to_pandas()
        return df

    def execute(self, query: str):
        self.client.query(query)



@dataclass
class CSVConnector:
    uri: str

    def load(self):
        return pd.write_csv(self.uri)

    def extract(self) -> pd.DataFrame:
        df = pd.read_csv(self.uri)

        return df
