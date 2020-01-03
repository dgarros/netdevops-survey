"""
(c) 2019 Damien Garros

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
  http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import pandas as pd
import base64
import math
import argparse
import os

__author__ = "Damien Garros <dgarros@gmail.com>"


def main():

    my_parser = argparse.ArgumentParser()
    my_parser.add_argument("--survey", action="store", type=int, required=True)
    my_parser.add_argument("--question", action="store", type=str, required=True)

    args = my_parser.parse_args()

    result_file = f"../results/{args.survey}.tsv"

    if not os.path.isfile(result_file):
        print(f"ERROR: Unable to find the result file at {result_file}")
        exit(1)

    # Load the results as a Pandas DataFrame and check if the question is present
    df = pd.read_csv(f"../results/{args.survey}.tsv", sep="\t", header=0)

    if args.question not in df.columns:
        print("ERROR: Unable to find the question in the document")
        exit(1)

    responses = {}
    for resp in list(df[args.question]):

        if not resp or (isinstance(resp, float) and math.isnan(resp)):
            continue

        if isinstance(resp, str):
            values = resp.split(",")
        else:
            values = [str(resp)]

        for value in values:

            b64v = base64.encodebytes(value.strip().encode())

            if b64v not in responses.keys():
                responses[b64v] = 1
            else:
                responses[b64v] += 1

    tmp = [{"resp": k, "count": v} for k, v in responses.items()]
    sorted_resps = sorted(tmp, key=lambda i: i["count"], reverse=True)

    for response in sorted_resps:
        print(f"{response['count']} - {base64.decodebytes(response['resp']).decode()}")


if __name__ == "__main__":
    main()
