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

import pygal
import os
import sys
import yaml
import argparse
import logging
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, func
from collections import OrderedDict

from pygal.style import CleanStyle, Style

import sys

sys.path.append("../")
from lib.schema import (
    Surveys,
    Questions,
    QuestionResponses,
    SurveyQuestions,
    SurveyResponses,
    Choices,
    Base,
)
from lib.query import *
from lib.graph import *

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



def main():

    my_parser = argparse.ArgumentParser()

    my_parser.add_argument("--debug", action="store_true")
    my_parser.add_argument(
        "--out", action="store", type=str, default="../graphs"
    )
    my_parser.add_argument("--format", action="store", type=str, default="png,svg")

    my_parser.add_argument(
        "--db", action="store", type=str, default="../results/netdevops_survey.sqlite3"
    )

    args = my_parser.parse_args()

    out_format = args.format.split(',')

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)8s - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)8s - %(message)s")

    engine = create_engine(f"sqlite:///{args.db}")
    Base.metadata.bind = engine
    Session = sessionmaker(bind=engine)
    session = Session()

    surveys = session.query(Surveys).all()
    questions = session.query(Questions).all()

    for question in questions:

        sqs = (
            session.query(SurveyQuestions)
            .filter(SurveyQuestions.question == question)
            .all()
        )

        # -------------------------------------------------------------------
        # Single SQ Graphs
        # -------------------------------------------------------------------
        for sq in sqs:

            if question.type == "Multiple choice grid" and "trend" in question.id:

                chart = stacked_graph_gsq(session, sq, TRENDS_ORDER)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_stack"
                generate_graphs(chart, filename, args.out, out_format)

            elif question.type == "Multiple choice grid" and "change" in question.id:

                chart = stacked_graph_gsq(session, sq, CHANGES_ORDER)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_stack"
                generate_graphs(chart, filename, args.out, out_format)

            elif question.type == "Multiple choice grid" and "language" in question.id:

                chart = stacked_graph_gsq(session, sq, USAGE_ORDER)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_stack"
                generate_graphs(chart, filename, args.out, out_format)

            elif question.type == "Multiple choice":

                chart = bar_graph_tools(session, sq, percentage=False)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_tool"
                generate_graphs(chart, filename, args.out, out_format)

                chart = bar_graph_tools(session, sq, percentage=True)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_tool_perc"
                generate_graphs(chart, filename, args.out, out_format)

                chart = count_distribution(session, sq)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_count_distribution"
                generate_graphs(chart, filename, args.out, out_format)

            elif question.type == "Single choice":

                chart = bar_graph(session, sq, percentage=False, sort=False)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_bar"
                generate_graphs(chart, filename, args.out, out_format)

                chart = bar_graph(session, sq, percentage=True, sort=False)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_bar_perc"
                generate_graphs(chart, filename, args.out, out_format)

                chart = pie_graph(session, sq)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_pie"
                generate_graphs(chart, filename, args.out, out_format)

            # -------------------------------------------------------------------
            # Comparisons by segment
            # -------------------------------------------------------------------
            if (
                question.type == "Multiple choice"
                and "troubleshoot" not in sq.question_id
            ):

                chart = compare_results_nwk_size(session, sq)
                filename = (
                    f"netdevops_survey_{sq.survey_id}_{sq.question_id}_compare_size"
                )
                generate_graphs(chart, filename, args.out, out_format)

        # -------------------------------------------------------------------
        # YoY comparisons
        # -------------------------------------------------------------------

        if question.type == "Multiple choice" and len(sqs) > 1:

            chart = compare_results_over_time_hbar(session, question)
            filename = f"netdevops_survey_{question.id}_compare"
            generate_graphs(chart, filename, args.out, out_format)

            chart = compare_count_distribution(session, question)
            filename = f"netdevops_survey_{question.id}_nbr_resp"
            generate_graphs(chart, filename, args.out, out_format)

        if question.type == None and question.parent_id and len(sqs) > 1:

            if "trend" in question.parent_id:
                chart = compare_results_over_time_sbar(session, question, TRENDS_ORDER)
            else:
                chart = compare_results_over_time_hbar(session, question)

            filename = f"netdevops_survey_{question.parent_id}_{question.id}_compare"
            generate_graphs(chart, filename, args.out, out_format)


if __name__ == "__main__":
    main()
