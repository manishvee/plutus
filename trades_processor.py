import glob
import io

import polars as pl 
from google.cloud import bigquery

def extract_new_trades():
    file_paths = glob.glob("/Users/manishvasu/Downloads/tradebook*.csv")
    df = pl.read_csv(file_paths[0])

    df = df.select(pl.col("symbol"),
                   pl.col("isin"),
                   pl.col("trade_date").str.to_date(format="%d/%m/%y"),
                   pl.col("exchange"),
                   pl.col("trade_type"),
                   pl.col("quantity").cast(pl.Int64),
                   pl.col("price"))

    df = df.with_columns(pnl=pl.lit(None).cast(pl.Float64))

    return df


def load_new_trades(df):
    client = bigquery.Client()

    with io.BytesIO() as stream:
        df.write_parquet(stream)
        stream.seek(0)
        job = client.load_table_from_file(
            stream,
            destination='plutus-424506.equity.equity-pnl',
            project='plutus-424506',
            job_config=bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.PARQUET,
            ),
        )
    job.result() 



def extract_existing_trades():
    client = bigquery.Client()

    QUERY = (
        'SELECT * FROM `plutus-424506.equity.equity-pnl`'
        )
    query_job = client.query(QUERY)
    rows = query_job.result()

    df = pl.from_arrow(rows.to_arrow())

    return df


if __name__ == "__main__":
    new_trades = extract_new_trades()

    load_new_trades(new_trades)