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

from collections import defaultdict

from .schema import (
    QuestionResponses,
    SurveyQuestions,
    Choices,
    Base,
)
from sqlalchemy import func, text

from pandas import DataFrame
import pandas as pd


def get_sq_results(session, sq, percentage=False, sort=True, min_count=None) -> DataFrame:
    """
    Get the number of occurrence per response for a given SurveyQuestion

    Return the results as a pandas DataFrame with one column called "value"
    """
    res = (
        session.query(Choices.desc, func.count(QuestionResponses.choice_id))
        .join(Choices)
        .filter(QuestionResponses.survey_question == sq)
        .group_by(QuestionResponses.choice_id)
        .all()
    )

    if min_count:
        res = [r for r in res if r[1] >= min_count]

    labels = [r[0] for r in res]

    if percentage:
        count = get_nbr_partipants(session, sq)
        values = {"value": [round((r[1] / count) * 100, 3) for r in res]}
    else:
        values = {"value": [r[1] for r in res]}

    df = DataFrame(values, index=labels)

    if sort:
        return df.sort_values("value")
    else:
        return df


def get_sq_results_group_by_sq(session, sq1, sq2, percentage=True) -> DataFrame:
    """
    Get Results for a given SurveyQuestion group by the responses from a second SurveyQuestion
    For example:
        Group result of "what operation is automated .. " by network size

    Return the results as a pandas DataFrame with one column per group
    """

    groups = {}

    # Collect responses from SQ2 to build Groups
    # For each valid response, get a list of surveyresponse_id
    sq2_res = (
        session.query(Choices.desc, QuestionResponses.surveyresponse_id)
        .join(Choices)
        .filter(QuestionResponses.survey_question == sq2)
        .all()
    )

    for r in sq2_res:
        if r[0] not in groups:
            groups[r[0]] = dict(ids=list(), df=None)
        groups[r[0]]["ids"].append(r[1])

    # For each group, get the results for SQ1 and save the result in a DataFrame
    for group_name, group in groups.items():
        res = (
            session.query(Choices.desc, func.count(QuestionResponses.choice_id))
            .join(Choices)
            .filter(
                QuestionResponses.survey_question == sq1,
                QuestionResponses.surveyresponse_id.in_(tuple(group["ids"])),
            )
            .group_by(QuestionResponses.choice_id)
            .all()
        )

        labels = [r[0] for r in res]

        if percentage:
            count = len(group["ids"])
            values = {"value": [round((r[1] / count) * 100, 3) for r in res]}
        else:
            values = {"value": [r[1] for r in res]}

        groups[group_name]["df"] = pd.DataFrame(values, index=labels)

    # Combine all the dataframe together
    dfs = [g["df"] for g in groups.values()]
    df = pd.concat(dfs, axis=1, sort=True)
    df.columns = list(groups.keys())

    return df


def get_q_results_over_time(session, question, sqs=None, lowercase_index=False, percentage=True, min_count=None):
    """
    Get results for a given question on all surveys

    Return results as a DataFrame with one column per survey
    """

    if not sqs:
        sqs = session.query(SurveyQuestions).filter(SurveyQuestions.question == question).all()

    responses = {}
    for sq in sqs:
        responses[sq.survey_id] = get_sq_results(session, sq, percentage=percentage, min_count=min_count)
        if lowercase_index:
            responses[sq.survey_id].index = responses[sq.survey_id].index.str.lower()

    # Combine all the dataframe together
    dfs = [r for r in responses.values()]
    df = pd.concat(dfs, axis=1, sort=True)
    df.columns = list(responses.keys())

    # Calculate mean by row
    # df.mean(1)
    ## Sort Index by mean values
    # df.reindex(df.mean(1).sort_values(0).index, axis=0)

    return df.fillna(0)


def get_gsq_results(session, gsq: SurveyQuestions, percentage=True, order_by=None) -> DataFrame:
    """
    Get results for a SurveyQuestions of type Multiple choice Grid

    Return the result as a pandas DataFrame will one option per column
    """
    sqs = session.query(SurveyQuestions).filter_by(parent_id=gsq.id).all()

    responses = {}
    for sq in sqs:
        responses[sq.text] = get_sq_results(session, sq, percentage=percentage)

    # Combine all the dataframe together
    dfs = [r for r in responses.values()]
    df = pd.concat(dfs, axis=1, sort=True)
    df.columns = list(responses.keys())

    return df


def get_nbr_responses(session, sq):
    return session.query(QuestionResponses).filter_by(surveyquestion_id=sq.id).count()


def get_nbr_partipants(session, sq):

    return (
        session.query(QuestionResponses)
        .filter_by(surveyquestion_id=sq.id)
        .group_by(QuestionResponses.surveyresponse_id)
        .count()
    )


def get_sq_stats(session, sq):

    res = (
        session.query(func.count(QuestionResponses.choice_id))
        .filter(QuestionResponses.survey_question == sq)
        .group_by(QuestionResponses.surveyresponse_id)
        .all()
    )

    responses = [x[0] for x in res]
    nbr_responses = len(responses)
    avg_responses = sum(responses) / len(responses)
    min_responses = min(responses)
    max_responses = max(responses)

    return (nbr_responses, round(avg_responses, 2), min_responses, max_responses)


def get_sq_nbr_responses_count(session, sq, percentage=True) -> DataFrame:
    """
    Return the number of responses per count number for a given
    Multi choice SurveyQuestions

    Return the results as a pandas DataFrame with one column called "value"
    """

    res = (
        session.query(func.count(QuestionResponses.choice_id))
        .filter(QuestionResponses.survey_question == sq)
        .group_by(QuestionResponses.surveyresponse_id)
        .all()
    )

    nbr_responses = len(res)

    counts = defaultdict(int)

    for r in res:
        counts[r] += 1

    if percentage:
        df = pd.DataFrame(
            {"value": [round((v / nbr_responses) * 100, 3) for v in list(counts.values())]}, index=counts.keys()
        )
    else:
        df = pd.DataFrame({"value": list(counts.values())}, index=counts.keys())

    return df.sort_index()


def get_q_nbr_resp_over_time(session, question, sqs=None) -> DataFrame:

    if not sqs:
        sqs = session.query(SurveyQuestions).filter(SurveyQuestions.question == question).all()

    responses = {}
    for sq in sqs:
        responses[sq.survey_id] = get_sq_nbr_responses_count(session, sq, percentage=True)

    # Combine all the dataframe together
    dfs = [r for r in responses.values()]
    df = pd.concat(dfs, axis=1, sort=True)
    df.columns = list(responses.keys())

    # Calculate mean by row
    # df.mean(1)
    ## Sort Index by mean values
    # df.reindex(df.mean(1).sort_values(0).index, axis=0)

    return df
