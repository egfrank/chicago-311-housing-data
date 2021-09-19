import argparse
import csv
import json
import os
import pathlib
import sys

import googlemaps
import pandas as pd
from dotenv import load_dotenv


def write_csv(filename, data_dict):
    with open(filename, "w", newline="") as outfile:
        headers = list(data_dict[0].keys())
        writer = csv.DictWriter(outfile, headers, delimiter=",", quotechar='"')
        writer.writeheader()
        writer.writerows(data_dict)


def xlsx_to_csv(filename, output_name):
    read_file = pd.read_excel(filename, engine="openpyxl")
    read_file.to_csv(output_name, index=None, header=True)


cwd = pathlib.Path().resolve()

XL_FILE_NAME = pathlib.PurePath.joinpath(cwd, "foia_response.xlsx")
CSV_FILE_NAME = pathlib.PurePath.joinpath(cwd, "foia.csv")


xlsx_to_csv(XL_FILE_NAME, CSV_FILE_NAME)


# Load API KEY from .env
load_dotenv()
gmaps = googlemaps.Client(os.getenv("GOOGLE_MAPS_API_KEY"))

with open(CSV_FILE_NAME, newline="") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
    blocks = [row for row in reader]


located_blocks = []
not_located_blocks = []


output_data = {}

counter = 1
for entry in blocks:

    del entry["Unnamed: 1"]
    del entry["Unnamed: 12"]
    entry["Street Block"] = entry["Street Block"].title()

    if len(entry["Street Block"]) < 4:
        continue

    entry["Zip Code"] = int(entry["Zip Code"].split(".")[0])

    street_block = entry["Street Block"]
    zipcode = entry["Zip Code"]

    entry["_key"] = f"{street_block}-{zipcode}"

    lookup = f"{street_block}, {zipcode}"

    print(f"looking up {street_block}, {zipcode}")

    result = gmaps.geocode(f"{street_block}, Chicago, IL, {zipcode}")
    counter += 1

    if len(result) == 0:
        not_located_blocks.append(entry)
        continue

    result = result[0]
    entry["_address"] = result["formatted_address"]
    entry["_latitude"] = result["geometry"]["location"]["lat"]
    entry["_longitude"] = result["geometry"]["location"]["lng"]

    if lookup not in output_data:
        entry["_count"] = 1
        output_data[lookup] = entry
    else:
        output_data[lookup]["_count"] += 1

write_csv("geolocated_blocks.csv", list(output_data.values()))
if len(not_located_blocks) > 0:
    write_csv("not_located_blocks.csv", not_located_blocks)
