
This repository is the home of the Netdevops survey, The goal of this survey is to collect information to understand how network operators and engineers are using automation to operate their network today. 

There are numerous surveys available that present how Sysadmin and DevOps professionals manage and deploy servers. In contrast, less is known about the state of “network operations through automation”. This 3rd edition of the Netdevops survey seeks to address that gap, and gather a 2020 snapshot.

# Vendor Neutral and Collaborative

This survey has been designed to be vendor neutral and collaborative. 
Everyone is welcome to participate in the definition of the questionnaire and the definition of the report.

Questions and feedback can be provided via Github issue or via the NetworkToCode Slack channel. 
You can sign up and join the Slack community here: http://slack.networktocode.com/

# 2020 Survey open!
Please take a few minutes and participate in the [2020 Edition](http://bit.ly/netdevops-survey-2020)

# Past Reports

- [2016](https://dgarros.github.io/netdevops-survey/reports/2016)
- [2019](https://dgarros.github.io/netdevops-survey/reports/2019)

## 2020 Timing
* September 1st to September 30th : Definition of the questionnaire (github)
* Oct 1st to October 30th : Survey open for response
* October 31st to November 30th : Results cleanup
* December 3rd : Results publication

## Core Team
* Francois Caen
* Damien Garros

# Previous Editions

Previous editions of the netdevops survey took place in Fall 2016 and 2019.
* The raw results are available in the results folder in TSV format or in a SQLite database 

## Core Team
- Jason Frazier
- David Barroso
- Pete Lumbis
- Jason Edelman
- Senthil Kumar Ganesan
- Damien Garros

# Project Organization

## Tools Selection and Requirements
The netdevops survey can be broken down in 4 steps, each with it's own set of requirements

### Questionnaire definition
Define the content and the format of the questionnaire for an upcoming survey.  
Define the list of sections, questions and associated responses.
The definition of the questionnaire aim at beeing as open as possible. Anyone should be able to comment on the existing proposal and should be able to propose some modifications. 
To be accepted a modification needs to be reviewed and approved by at least one maintainer

**Proposed solution**: Github 

### Responses collection
Web interface to collect the responses to the survey.  
The interface should be accessible on both desktop and mobile browser.  
No authentification should be required.

**Proposed solution**: Google Form 

### Raw Results
Survey results will be available in raw format for anyone to analyze (in 2016 the results were available in a Google Sheet).
Ideally as we start to have multiple editions of the survey, it would be interesting to have the results available in a common format/place.

**Proposed solution**: TSV file saved in Github 

### Reports
if possible it would be great to have a solution to:
- Collaboratively create a report with nice graphics 
- Distribute and update this report (web UI?)

**Proposed solution**: Markdown files in Github + Graphs generated with Pygal
