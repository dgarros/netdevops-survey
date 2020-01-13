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
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

question_choices = Table(
    "question_choices",
    Base.metadata,
    Column("surveyquestion_id", Integer, ForeignKey("survey_questions.id")),
    Column("choice_id", Integer, ForeignKey("choices.id")),
)


class Surveys(Base):
    """
    Collection of Survey.
    A Survey represent a specific questionnaire that was open for response during for a limited time
    2016 Edition is a survey, as well as the 2019 Edition
    """

    __tablename__ = "surveys"

    id = Column(String(50), primary_key=True)
    desc = Column(String(250), nullable=True)

    def __repr__(self):
        return f"Survey {self.id}"


class Questions(Base):
    """
    Collection of Question.
    A Question represent a specific question that can be part of multiple survey.
    A Question is implemented in a specific Survey as a SurveyQuestions
    A Question can be of Type:
      - Single choice
      - Multiple choice
      - Multiple choice grid 
    Since a `Multiple choice grid` is a group of single choice question, 
    it's possible for Questions to be related to eachother in a parent/child relationship
    """

    __tablename__ = "questions"

    id = Column(String(50), primary_key=True)
    desc = Column(String(250), nullable=True)
    type = Column(String(250), nullable=True)
    parent_id = Column(String(50), ForeignKey("questions.id"), nullable=True)

    parent = relationship("Questions")

    def __repr__(self):
        if self.parent_id:
            return f"Question [{self.parent_id}] -> {self.id}"
        else:
            return f"Question {self.id}"


class SurveyQuestions(Base):
    """
    Collection of SurveyQuestion.
    A SurveyQuestion is the implementation of a specific question in a Survey. 
    The Role of a SurveyQuestion is to track, the specificty of a question in each survey.
    The title of 2 SurveyQuestions can be different between 2 differents surveys
    The responses associated with a question can be different too between 2 differents surveys
    """

    __tablename__ = "survey_questions"

    id = Column(Integer, primary_key=True)
    survey_id = Column(String(50), ForeignKey("surveys.id"))
    question_id = Column(String(50), ForeignKey("questions.id"))
    text = Column(String(250), nullable=True)
    parent_id = Column(Integer, ForeignKey("survey_questions.id"), nullable=True)

    survey = relationship(Surveys)
    question = relationship(Questions)
    parent = relationship("SurveyQuestions")

    choices = relationship(
        "Choices", secondary=question_choices, back_populates="survey_questions"
    )

    def __repr__(self):
        return f"SurveyQuestion '{self.survey_id}::{self.question_id}''"


class Choices(Base):
    """
    Collection of Choices
    A choice is a simple text field that can be used either in a SurveyQuestion or a QuestionResponses
    """

    __tablename__ = "choices"

    id = Column(Integer, primary_key=True)
    desc = Column(String(250), nullable=False)

    survey_questions = relationship(
        "SurveyQuestions", secondary=question_choices, back_populates="choices"
    )

    def __repr__(self):
        return f"Choice '{self.desc}' ({self.id})"


class SurveyResponses(Base):
    """
    Collection of SurveyResponses
    A SurveyResponse track all the responses of a single individual
    """

    __tablename__ = "survey_responses"

    id = Column(String(50), primary_key=True)


class QuestionResponses(Base):
    """
    Collection of QuestionResponses
    A QuestionResponse track the responses to specific surveyquestion by a given surveyresponse (person)
    """

    __tablename__ = "question_responses"

    id = Column(Integer, primary_key=True)
    surveyresponse_id = Column(Integer, ForeignKey("survey_responses.id"))
    surveyquestion_id = Column(String(50), ForeignKey("survey_questions.id"))
    choice_id = Column(Integer, ForeignKey("choices.id"))

    survey_response = relationship(SurveyResponses)
    survey_question = relationship(SurveyQuestions)
    choice = relationship(Choices)
