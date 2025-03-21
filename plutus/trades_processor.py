import glob
from collections import defaultdict

import pandas as pd
from config import BQ_DATASET_NAME, BQ_PROJECT_NAME


def extract_new_trades(path):
    file_paths = glob.glob(path)
    print(f"Extracting trades from the following {len(file_paths)} file(s):")
    for f in file_paths:
        print(f)

    dfs = [CSVConnector(f).extract() for f in file_paths]
    df = pd.concat(dfs, ignore_index=True)

    print(f"Found {df.shape[0]} new trades")
    return df


def get_existing_trades():
    QUERY = """
        SELECT 
            * 
        FROM 
            `plutus-424506.equity.pnl`
        WHERE 
            trade_type = 'buy'
            and balance > 0
        """

    print("Extracting existing trades from BigQuery")
    existing_trades = bq_conn.extract(QUERY)
    print(f"Found {existing_trades.shape[0]} unbalanced trades")

    return existing_trades


def update_existing_trades(update_records):
    print(f"Updating {update_records.shape[0]} existing trades")
    for idx, data in update_records.iterrows():
        query = f"""
            UPDATE 
                `plutus-424506.equity.pnl` 
            SET 
                pnl = {data['pnl']}, 
                balance = {data['balance']} 
            WHERE 
                trade_id = '{data['trade_id']}'
            """
        bq_conn.execute(query)
    print("Finished updating existing trades")


def process_trades(trades_df):
    trades_queue = defaultdict(list)
    for idx, data in trades_df.iterrows():
        trade_id, symbol, balance, quantity, price = (
            data["trade_id"],
            data["symbol"],
            data["balance"],
            data["quantity"],
            data["price"],
        )

        if data["trade_type"] == "buy":
            trades_queue[symbol].append([trade_id, balance or quantity, price])

        else:
            pnl = 0
            while quantity > 0:
                if quantity >= trades_queue[symbol][0][1]:
                    pnl += trades_queue[symbol][0][1] * (
                        price - trades_queue[symbol][0][2]
                    )
                    quantity -= trades_queue[symbol][0][1]

                    buy_to_update = trades_queue[symbol].pop(0)
                    trades_df.at[buy_to_update[0], "balance"] = 0

                else:
                    pnl += quantity * (price - trades_queue[symbol][0][2])
                    trades_queue[symbol][0][1] = trades_queue[symbol][0][1] - quantity
                    quantity = 0

            trades_df.at[trade_id, "pnl"] = pnl

    for value in trades_queue.values():
        for trade in value:
            trades_df.at[trade[0], "balance"] = trade[1]

    return trades_df


if __name__ == "__main__":
    new_trades = extract_new_trades("/Users/manishvasu/Downloads/Tradebook*.csv")
    new_trades = new_trades[
        [
            "trade_id",
            "symbol",
            "isin",
            "trade_date",
            "quantity",
            "price",
            "trade_type",
            "order_execution_time",
        ]
    ]
    new_trades["pnl"], new_trades["balance"] = None, None
    new_trades["trade_date"] = pd.to_datetime(new_trades["trade_date"])
    new_trades["order_execution_time"] = pd.to_datetime(
        new_trades["order_execution_time"]
    )

    bq_conn = BigQueryConnector(BQ_PROJECT_NAME, BQ_DATASET_NAME)
    existing_trades = get_existing_trades()

    trades_df = pd.concat([existing_trades, new_trades], ignore_index=True)
    trades_df = trades_df.sort_values(by="order_execution_time")
    trades_df.index = trades_df["trade_id"]
    print(f"Processing PnL for {trades_df.shape[0]} trades")

    trades_df = process_trades(trades_df)

    update_records = trades_df[trades_df["trade_id"].isin(existing_trades["trade_id"])]
    insert_records = trades_df[~trades_df["trade_id"].isin(existing_trades["trade_id"])]

    update_existing_trades(update_records)

    print(f"Inserting {insert_records.shape[0]} new trades")
    bq_conn.load(insert_records, "pnl")
    print("Finished inserting new trades")
