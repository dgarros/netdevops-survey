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
import yaml
import argparse
import logging
import pandas as pd
import math

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from schema import *

__author__ = "Damien Garros <dgarros@gmail.com>"

questions_pending_cleaning = {
    "2016": [
        "env-vendors",
        "env-type",
        "env-virtual-network",
        "env-server-automation",
        "env-location",
        "operation-automated",
        "config-track-changes",
        "config-gen-deploy",
        "troubleshoot",
        "software-upgrade",
        "software-validation",
        "anomaly-detection",
    ],
    "2019": [
        "env-vendors",
        "env-virtual-network",
        "env-server-automation",
        "operation-automated",
        "software-validation",
        "anomaly-detection-sources",
        "anomaly-detection-signal",
    ],
}


def load_question(survey_id, engine):

    Session = sessionmaker(bind=engine)
    session = Session()

    data = yaml.load(
        open(f"../questionnaire/{survey_id}/questions.yaml"), Loader=yaml.FullLoader
    )

    # ----------------------------------------------------------------------
    # Check if survey exist, or create it
    # ----------------------------------------------------------------------
    survey = session.query(Surveys).get(survey_id)
    if not survey:
        survey = Surveys(id=survey_id, desc=f"{survey_id} edition")
        session.add(survey)
        logging.info(f"Survey ADDED : {survey_id}")

    # ----------------------------------------------------------------------
    # Import Data from questionnaire
    # ----------------------------------------------------------------------
    for section in data:
        for question_data in section["questions"]:
            if "id" not in question_data.keys():
                logging.warning(
                    f"Question SKIPPED : missing ID : {question_data['title']}"
                )
                continue

            if "type" not in question_data.keys():
                logging.warning(
                    f"Question SKIPPED : missing TYPE : {question_data['title']}"
                )
                continue

            question_data["id"]

            # -------------------------------------------------------------------
            # Get or Create Question and SurveyQuestion
            # -------------------------------------------------------------------
            question = session.query(Questions).get(question_data["id"])
            if not question:
                question = Questions(
                    id=question_data["id"],
                    desc=question_data["title"],
                    type=question_data["type"],
                )
                session.add(question)
                logging.info(f"Question ADDED {question.id}")

            survey_question = (
                session.query(SurveyQuestions)
                .filter_by(survey_id=survey.id, question_id=question.id)
                .first()
            )
            if not survey_question:
                survey_question = SurveyQuestions(
                    survey_id=survey.id, question_id=question.id, text=question.desc
                )
                session.add(survey_question)
                logging.info(f"SurveyQuestions ADDED {survey.id}::{question.id}")

            # -------------------------------------------------------------------
            # Load : Multiple choice and Single Choice questions
            # -------------------------------------------------------------------
            if question_data["type"].strip() in ["Multiple choice", "Single choice"]:

                for choice_str in question_data["responses"]:
                    choice = session.query(Choices).filter_by(desc=choice_str).first()
                    if not choice:
                        choice = Choices(desc=choice_str)
                        session.add(choice)
                        logging.debug(f"Choice ADDED {choice_str}")

                    if choice not in survey_question.choices:
                        survey_question.choices.append(choice)

            # -------------------------------------------------------------------
            # Load : Multiple choice grid questions
            # -------------------------------------------------------------------
            elif question_data["type"].strip() in ["Multiple choice grid"]:

                grid_choices = []
                for choice_str in question_data["options"]:
                    choice = session.query(Choices).filter_by(desc=choice_str).first()
                    if not choice:
                        choice = Choices(desc=choice_str)
                        session.add(choice)
                        logging.debug(f"Choice ADDED {choice_str}")

                    grid_choices.append(choice)

                for grid_question_data in question_data["responses"]:

                    if not isinstance(grid_question_data, dict):
                        logging.warning(
                            f"Grid question SKIPPED : not a dict ({grid_question_data})"
                        )
                        continue

                    if "id" not in grid_question_data.keys():
                        logging.warning(
                            f"Grid question SKIPPED : id is missing ({grid_question})"
                        )
                        continue

                    if (
                        "text" not in grid_question_data.keys()
                        or grid_question_data["text"] == None
                    ):
                        logging.warning(
                            f"Grid question SKIPPED : text is missing ({grid_question_data})"
                        )
                        continue

                    grid_question_id = f"{question.id}-{grid_question_data['id']}"

                    grid_question = session.query(Questions).get(grid_question_id)
                    if not grid_question:
                        grid_question = Questions(
                            id=grid_question_id,
                            desc=grid_question_data["text"],
                            parent_id=question.id,
                        )
                        session.add(grid_question)
                        logging.info(f"Grid Question ADDED {grid_question.id}")

                    grid_survey_question = (
                        session.query(SurveyQuestions)
                        .filter_by(survey_id=survey.id, question_id=grid_question.id)
                        .first()
                    )
                    if not grid_survey_question:
                        grid_survey_question = SurveyQuestions(
                            survey_id=survey.id,
                            question_id=grid_question.id,
                            text=grid_question_data["text"],
                            parent_id=survey_question.id,
                        )
                        session.add(grid_survey_question)
                        logging.info(
                            f"Grid Survey Question ADDED {survey.id}::{grid_question.id}"
                        )

                    for c in grid_choices:
                        if c not in grid_survey_question.choices:
                            grid_survey_question.choices.append(c)

            elif question_data["id"] != "feedback":
                logging.warning(
                    f"Question SKIPPED : wrong TYPE : {question_data['title']}"
                )
                continue

    session.commit()


def load_responses(survey_id, engine):

    result_file = f"../results/{survey_id}.tsv"

    if not os.path.isfile(result_file):
        logging.error(f"Unable to find the result file at {result_file}")
        exit(1)

    df = pd.read_csv(result_file, sep="\t", header=0)

    # Build list of questions to import based on questions_pending_cleaning
    if survey_id in questions_pending_cleaning:
        question_to_exclude = questions_pending_cleaning[survey_id]
    else:
        question_to_exclude = []

    question_to_exclude.extend(["Timestamp", "feedback"])

    questions_list = [q for q in list(df.columns) if q not in question_to_exclude]

    Session = sessionmaker(bind=engine)
    session = Session()

    survey = session.query(Surveys).get(survey_id)
    if not survey:
        logging.error(f"Unable to find the survey for {survey_id} in the database")
        exit(1)

    responses = {}

    for question_id in questions_list:

        survey_question = (
            session.query(SurveyQuestions)
            .filter_by(survey_id=survey.id, question_id=question_id)
            .first()
        )
        if not survey_question:
            logging.error(
                f"ERROR, Unable to find the survey_question for {survey.id} / {question_id}"
            )
            exit(1)

        responses = list(df[question_id])

        for idx in range(0, len(df.index)):

            sr_id = f"{survey.id}-{idx}"

            sr = session.query(SurveyResponses).get(sr_id)
            if not sr:
                sr = SurveyResponses(id=sr_id)
                logging.info(f"SurveyResponses ADDED {sr_id}")
                session.add(sr)

            resp = responses[idx]

            if not resp or (isinstance(resp, float) and math.isnan(resp)):
                continue

            values = resp.split(",")

            for value in values:

                choice = session.query(Choices).filter_by(desc=value.strip()).first()
                if not choice:
                    choice = Choices(desc=value.strip())
                    session.add(choice)
                    logging.debug(f"Choice ADDED {value.strip()}")

                qr = (
                    session.query(QuestionResponses)
                    .filter_by(
                        surveyquestion_id=survey_question.id,
                        surveyresponse_id=sr.id,
                        choice_id=choice.id,
                    )
                    .first()
                )
                if not qr:
                    qr = QuestionResponses(
                        surveyquestion_id=survey_question.id,
                        surveyresponse_id=sr.id,
                        choice_id=choice.id,
                    )
                    logging.debug(
                        f"QuestionResponses ADDED {survey_question.id} - {sr.id} - {choice}"
                    )
                    session.add(qr)

    logging.info("Saving the responses in the database ... ")
    session.commit()


def main():

    my_parser = argparse.ArgumentParser()
    my_parser.add_argument("--survey", action="store", type=int, required=True)
    my_parser.add_argument("--load-question", action="store_true")
    my_parser.add_argument("--load-response", action="store_true")
    my_parser.add_argument("--init", action="store_true")
    my_parser.add_argument("--debug", action="store_true")
    my_parser.add_argument(
        "--db", action="store", type=str, default="../results/netdevops_survey.sqlite3"
    )

    args = my_parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)8s - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)8s - %(message)s")

    engine = create_engine(f"sqlite:///{args.db}")
    Base.metadata.bind = engine
    Session = sessionmaker(bind=engine)

    if args.init:
        Base.metadata.create_all(engine)

    if args.load_question:
        load_question(survey_id=args.survey, engine=engine)

    if args.load_response:
        load_responses(survey_id=args.survey, engine=engine)


if __name__ == "__main__":
    main()
