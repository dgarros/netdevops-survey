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


def load_survey_result(survey_id, path="../results"):
    """
    Load the result in TSV formar and return a pandas DataFrame
    """

    result_file = f"{path}/{survey_id}.tsv"

    if not os.path.isfile(result_file):
        print(f"ERROR: Unable to find the result file at {result_file}")
        exit(1)

    # Load the results as a Pandas DataFrame and check if the question is present
    df = pd.read_csv(result_file, sep="\t", header=0)

    return df


def count_responses(datas):
    """
    Count number of occurrence for each response

    Return a pandas DataFrame
    """
    responses = {}
    for resp in datas:

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

    labels = [base64.decodebytes(k).decode() for k, v in responses.items()]
    values = [v for k, v in responses.items()]

    return pd.DataFrame(values, index=labels).sort_values(0, ascending=False)


def main():

    my_parser = argparse.ArgumentParser()
    my_parser.add_argument("--survey", action="store", type=int)
    my_parser.add_argument("--question", action="store", type=str, required=True)

    args = my_parser.parse_args()

    if args.survey:
        surveys = [args.survey]
    else:
        surveys = [2016, 2019]

    responses = {}

    for survey_id in surveys:
        result = load_survey_result(survey_id)

        if args.question not in result.columns:
            print(f"ERROR: Unable to find the question in the result for {survey_id}")
            exit(1)

        responses[survey_id] = count_responses(list(result[args.question]))

    dfs = [r for r in responses.values()]
    df = pd.concat(dfs, axis=1, sort=True)
    df.columns = list(responses.keys())

    print(df.sort_values(by=list(responses.keys())[0], ascending=False))


if __name__ == "__main__":
    main()
