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

netdevops_style_trends = Style(
    colors=("#E39A48", "#C9CAC9", "#77C780", "#00B814", "#067512"),
    label_font_size=20,
    major_label_font_size=16,
    value_font_size=20,
    value_label_font_size=20,
    # tooltip_font_size=18,
    title_font_size=40,
    legend_font_size=20,
)

netdevops_style_base = Style(
    colors=("#38761d", "#93c47d", "#77C780"),
    label_font_size=28,
    major_label_font_size=16,
    value_font_size=28,
    value_label_font_size=28,
    # tooltip_font_size=18,
    title_font_size=40,
    legend_font_size=34,
)


def compare_bar_graph(session, sqs, out, out_type=["png"]):

    results = OrderedDict()
    labels = []

    results = get_gsq_results(session, sq, percentage=True)

    # for sq in sqs:
    #     res = get_survey_question_results(session, sq, percentage=True)

    #     res = [x for x in res if x[1] > 1]

    #     sq_labels = [r[0] for r in res]
    #     results[sq.survey_id] = {
    #         "labels": sq_labels,
    #         "values": {r[0]: r[1] for r in res},
    #     }

    avg_results = {}
    surveys = list(results.keys())
    for survey_id, data in results.items():
        for label, value in data["values"].items():
            if label not in avg_results.keys():
                avg_results[label] = 0
                nbr_results = 0
                for s in surveys:
                    if label in results[s]["values"].keys():
                        nbr_results = +1
                        avg_results[label] = +results[s]["values"][label]

                avg_results[label] = avg_results[label] / nbr_results

    labels = sorted(avg_results, key=avg_results.__getitem__)

    title = sqs[0].text.replace("?", "?\n")

    bar_chart = pygal.HorizontalBar(
        legend_at_bottom=False,
        width=1920,
        height=1080,
        title=f"Netdevops Survey \n {title}",
        style=netdevops_style_base,
        x_title="%",
    )
    bar_chart.x_labels = map(str, labels)
    for survey_id, data in results.items():
        bar_chart.add(
            survey_id,
            [
                data["values"][label] if label in data["labels"] else None
                for label in labels
            ],
        )

    filename = (
        f"netdevops_survey_{sq.question_id}_comparison_{'_'.join(list(results.keys()))}"
    )

    if "png" in out_type:
        bar_chart.render_to_png(f"{out}/{filename}.png")

    logging.info(f"Generated {filename} {out_type}")


def main():

    my_parser = argparse.ArgumentParser()

    my_parser.add_argument("--debug", action="store_true")
    my_parser.add_argument(
        "--out", action="store", type=str, default="../results/graphs"
    )
    my_parser.add_argument("--format", action="store", type=list, default=["png"])

    my_parser.add_argument(
        "--db", action="store", type=str, default="../results/netdevops_survey.sqlite3"
    )

    args = my_parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)8s - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)8s - %(message)s")

    engine = create_engine(f"sqlite:///../results/netdevops_survey.sqlite3")
    # engine = create_engine(f"sqlite:///{args.db}")
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
                generate_graphs(chart, filename, args.out, args.format)

            elif question.type == "Multiple choice grid" and "change" in question.id:

                chart = stacked_graph_gsq(session, sq, CHANGES_ORDER)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_stack"
                generate_graphs(chart, filename, args.out, args.format)

            elif question.type == "Multiple choice grid" and "language" in question.id:

                chart = stacked_graph_gsq(session, sq, USAGE_ORDER)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_stack"
                generate_graphs(chart, filename, args.out, args.format)

            elif question.type == "Multiple choice":

                chart = bar_graph_tools(session, sq, percentage=False)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_tool"
                generate_graphs(chart, filename, args.out, args.format)

            elif question.type == "Single choice":

                chart = bar_graph(session, sq, percentage=False, sort=False)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_bar"
                generate_graphs(chart, filename, args.out, args.format)

                chart = pie_graph(session, sq)
                filename = f"netdevops_survey_{sq.survey_id}_{sq.question_id}_pie"
                generate_graphs(chart, filename, args.out, args.format)

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
                generate_graphs(chart, filename, args.out, args.format)

        # -------------------------------------------------------------------
        # YoY comparisons
        # -------------------------------------------------------------------

        if question.type == "Multiple choice" and len(sqs) > 1:

            chart = compare_results_over_time_hbar(session, question)
            filename = f"netdevops_survey_{question.id}_compare"
            generate_graphs(chart, filename, args.out, args.format)

        if question.type == None and question.parent_id and len(sqs) > 1:

            if "trend" in question.parent_id:
                chart = compare_results_over_time_sbar(session, question, TRENDS_ORDER)
            else:
                chart = compare_results_over_time_hbar(session, question)

            filename = f"netdevops_survey_{question.parent_id}_{question.id}_compare"
            generate_graphs(chart, filename, args.out, args.format)


# for i in range(len(questions)):
#     print(f"{i} - {questions[i]}")


if __name__ == "__main__":
    main()
