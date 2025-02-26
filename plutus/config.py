import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

BQ_PROJECT = os.environ.get("BQ_PROJECT")
BQ_DATASET = os.environ.get("BQ_DATASET")
