
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
from sqlalchemy import create_engine
 
Base = declarative_base()
 
question_choices = Table('question_choices', Base.metadata,
    Column('surveyquestion_id', Integer, ForeignKey('survey_questions.id')),
    Column('choice_id', Integer, ForeignKey('choices.id'))
)

class Surveys(Base):
    __tablename__ = 'surveys'
    
    id = Column(String(50), primary_key=True)
    desc = Column(String(250), nullable=True)

    def __repr__(self):
        return f"Survey {self.id}" 


class Questions(Base):
    __tablename__ = 'questions'

    id = Column(String(50), primary_key=True)
    desc = Column(String(250), nullable=True)
    type = Column(String(250), nullable=True)
    parent_id = Column(String(50), ForeignKey('questions.id'), nullable=True)

    parent = relationship("Questions")

    def __repr__(self):
        if self.parent_id:
            return f"Question [{self.parent_id}] -> {self.id}"
        else:
            return f"Question {self.id}"


class SurveyQuestions(Base):
    __tablename__ = 'survey_questions'

    id = Column(Integer, primary_key=True)
    survey_id = Column(String(50), ForeignKey('surveys.id'))
    question_id = Column(String(50), ForeignKey('questions.id'))
    text = Column(String(250), nullable=True)
    parent_id = Column(Integer, ForeignKey('survey_questions.id'), nullable=True)

    survey = relationship(Surveys)
    question = relationship(Questions)
    parent = relationship("SurveyQuestions")

    choices = relationship("Choices",
                         secondary=question_choices,
                         back_populates="survey_questions")

    def __repr__(self):
        return f"SurveyQuestion '{self.survey_id}::{self.question_id}''"


class Choices(Base):
    __tablename__ = 'choices'
    
    id = Column(Integer, primary_key=True)
    desc = Column(String(250), nullable=False)
    
    survey_questions = relationship("SurveyQuestions",
                        secondary=question_choices,
                        back_populates="choices")

    def __repr__(self):
        return f"Choice '{self.desc}' ({self.id})"

class SurveyResponses(Base):
    __tablename__ = 'survey_responses'

    id = Column(String(50), primary_key=True)
    # entry_date = Column(DateTime, nullable=True)
    # feedback = Column(String(500), nullable=True)

class QuestionResponses(Base): 
    __tablename__ = 'question_responses'

    id = Column(Integer, primary_key=True)
    surveyresponse_id = Column(Integer, ForeignKey('survey_responses.id'))
    surveyquestion_id = Column(String(50), ForeignKey('survey_questions.id'))
    choice_id = Column(Integer, ForeignKey('choices.id'))

    survey_response = relationship(SurveyResponses)
    survey_question = relationship(SurveyQuestions)
    choice = relationship(Choices)
