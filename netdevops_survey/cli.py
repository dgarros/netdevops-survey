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
import os
import sys
import base64
import math
import logging

import pandas as pd
import click
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from .schema import (
    Questions,
    SurveyQuestions,
    Base,
)
from .query import *
from .graph import *
from .manage_db import load_responses, load_question

__author__ = "Damien Garros <dgarros@gmail.com>"

ALL_SURVEYS = [2016, 2019, 2020]

TRENDS_ORDER = [
    "i don't know",
    "no interest",
    "thinking about it",
    "currently evaluating it",
    "already in production",
]

CHANGES_ORDER = [
    "not sure",
    "less than 1 per month",
    "1 to 5 per month",
    "1 to 5 per week",
    "more than 1 a day",
]

USAGE_ORDER = ["none", "a little", "a lot"]


def load_survey_result(survey_id, path="./results"):
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


@click.group()
def main():
    pass


@click.option("--survey", type=int)
@click.option("--question", type=str)
@main.command()
def analyze_tsv(survey, question):

    if survey:
        surveys = [survey]
    else:
        surveys = ALL_SURVEYS

    responses = {}

    for survey_id in surveys:
        result = load_survey_result(survey_id)

        if question not in result.columns:
            print(f"ERROR: Unable to find the question in the result for {survey_id}")
            exit(1)

        responses[survey_id] = count_responses(list(result[question]))

    dfs = [r for r in responses.values()]
    df = pd.concat(dfs, axis=1, sort=True)
    df.columns = list(responses.keys())

    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", None)

    # df.set_option('display.max_rows', None)
    # df.set_option('display.max_columns', None)
    # df.set_option('display.width', None)
    # df.set_option('display.max_colwidth', -1)

    print(df.sort_values(by=list(responses.keys())[0], ascending=False))


@click.option("--survey", type=int)
@click.option("--debug", "debug_mode", default=False, is_flag=True)
@click.option("--db", type=str, default="./results/netdevops_survey.sqlite3")
@click.option("--out", type=str, default="./results")
@click.option("--prefix", type=str, default="netdevops_survey")
@click.option("--yoy/--no-yoy", default=True, is_flag=True)
@click.option("--single/--no-single", default=True, is_flag=True)
@main.command()
def generate_graphs(survey, debug_mode, db, out, prefix, yoy, single):

    if debug_mode:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)8s - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)8s - %(message)s")

    engine = create_engine(f"sqlite:///{db}")
    Base.metadata.bind = engine
    Session = sessionmaker(bind=engine)
    session = Session()

    # surveys = session.query(Surveys).all()
    questions = session.query(Questions).all()

    if survey:
        surveys = [int(survey)]
    else:
        surveys = ALL_SURVEYS

    for question in questions:

        for survey in surveys:

            sq = (
                session.query(SurveyQuestions)
                .filter(SurveyQuestions.question == question, SurveyQuestions.survey_id == survey)
                .first()
            )

            if not sq:
                continue

            # -------------------------------------------------------------------
            # Single SQ Graphs
            # -------------------------------------------------------------------
            if single:
                sq = (
                    session.query(SurveyQuestions)
                    .filter(SurveyQuestions.question == question, SurveyQuestions.survey_id == survey)
                    .first()
                )

                if question.type == "Multiple choice grid" and "trend" in question.id:

                    chart = stacked_graph_gsq(session, sq, TRENDS_ORDER)
                    filename = f"{prefix}_{survey}_{sq.question_id}_stack"
                    out_dir = f"{out}/{survey}"
                    generate_graph(chart, filename, out_dir)

                elif question.type == "Multiple choice grid" and "change" in question.id:

                    chart = stacked_graph_gsq(session, sq, CHANGES_ORDER)
                    filename = f"{prefix}_{survey}_{sq.question_id}_stack"
                    out_dir = f"{out}/{survey}"
                    generate_graph(chart, filename, out_dir)

                elif question.type == "Multiple choice grid" and "language" in question.id:

                    chart = stacked_graph_gsq(session, sq, USAGE_ORDER)
                    filename = f"{prefix}_{survey}_{sq.question_id}_stack"
                    out_dir = f"{out}/{survey}"
                    generate_graph(chart, filename, out_dir)

                elif question.type == "Multiple choice":
                    chart = bar_graph_tools(session, sq, percentage=False)
                    filename = f"{prefix}_{survey}_{sq.question_id}_tool"
                    out_dir = f"{out}/{survey}"
                    generate_graph(chart, filename, out_dir)

                    chart = bar_graph_tools(session, sq, percentage=True)
                    filename = f"{prefix}_{survey}_{sq.question_id}_tool_perc"
                    out_dir = f"{out}/{survey}"
                    generate_graph(chart, filename, out_dir)

                    chart = count_distribution(session, sq)
                    filename = f"{prefix}_{survey}_{sq.question_id}_count_distribution"
                    out_dir = f"{out}/{survey}"
                    generate_graph(chart, filename, out_dir)

                elif question.type == "Single choice":

                    chart = bar_graph(session, sq, percentage=False, sort=False)
                    filename = f"{prefix}_{survey}_{sq.question_id}_bar"
                    out_dir = f"{out}/{survey}"
                    generate_graph(chart, filename, out_dir)

                    chart = bar_graph(session, sq, percentage=True, sort=False)
                    filename = f"{prefix}_{survey}_{sq.question_id}_bar_perc"
                    out_dir = f"{out}/{survey}"
                    generate_graph(chart, filename, out_dir)

                    chart = pie_graph(session, sq)
                    filename = f"{prefix}_{survey}_{sq.question_id}_pie"
                    out_dir = f"{out}/{survey}"
                    generate_graph(chart, filename, out_dir)

                # -------------------------------------------------------------------
                # Comparisons by segment
                # -------------------------------------------------------------------
                # if (
                #     question.type == "Multiple choice"
                #     and "troubleshoot" not in sq.question_id
                # ):

                #     chart = compare_results_nwk_size(session, sq)
                #     filename = (
                #         f"{prefix}_{survey}_{sq.question_id}_compare_size"
                #     )
                #     out_dir = f"{out}/{survey}"
                #     generate_graph(chart, filename, out_dir)

            # -------------------------------------------------------------------
            # YoY comparisons
            # -------------------------------------------------------------------
            if yoy:

                yoy_surveys = ALL_SURVEYS[0 : ALL_SURVEYS.index(survey) + 1]

                if len(yoy_surveys) == 1:
                    logging.debug("Skipping YoY graphs for %s because there is nothing to compare with", survey)
                    continue

                sqs = (
                    session.query(SurveyQuestions)
                    .filter(SurveyQuestions.question == question, SurveyQuestions.survey_id.in_(yoy_surveys))
                    .all()
                )

                if question.type == "Multiple choice" and len(sqs) > 1:

                    chart = compare_results_over_time_hbar(session, question, sqs=sqs)
                    filename = f"{prefix}_{survey}_{question.id}_compare"
                    out_dir = f"{out}/{survey}"
                    generate_graph(chart, filename, out_dir)

                    chart = compare_count_distribution(session, question, sqs=sqs)
                    filename = f"{prefix}_{survey}_{question.id}_nbr_resp"
                    out_dir = f"{out}/{survey}"
                    generate_graph(chart, filename, out_dir)

                if question.type == None and question.parent_id and len(sqs) > 1:

                    if "trend" in question.parent_id:
                        chart = compare_results_over_time_sbar(session, question, sqs=sqs, results_order=TRENDS_ORDER)
                    else:
                        chart = compare_results_over_time_hbar(session, question, sqs=sqs)

                    filename = f"{prefix}_{survey}_{question.parent_id}_{question.id}_compare"
                    out_dir = f"{out}/{survey}"
                    generate_graph(chart, filename, out_dir)


@click.option("--survey", type=int)
@click.option("--debug", default=False, is_flag=True)
@click.option("--load-question", "loadquestion", default=False, is_flag=True)
@click.option("--load-response", "loadresponse", default=False, is_flag=True)
@click.option("--init", default=False, is_flag=True)
@click.option("--db", type=str, default="./results/netdevops_survey.sqlite3")
@main.command()
def database(survey, debug, loadquestion, loadresponse, init, db):

    if debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)8s - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)8s - %(message)s")

    engine = create_engine(f"sqlite:///{db}")
    Base.metadata.bind = engine
    Session = sessionmaker(bind=engine)

    if survey:
        surveys = [survey]
    else:
        surveys = ALL_SURVEYS

    if init:
        Base.metadata.create_all(engine)

    if loadquestion:
        for survey in surveys:
            load_question(survey_id=survey, engine=engine)

    if loadresponse:
        for survey in surveys:
            load_responses(survey_id=survey, engine=engine)
