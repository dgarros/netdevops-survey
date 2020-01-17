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
import re
import logging

from pygal.style import CleanStyle, Style, LightenStyle

from .query import *

GREEN = "#38761D"
RED = "#B45F06"
TRENDS_COLOR = ("#E39A48", "#C9CAC9", "#77C780", "#00B814", "#067512")

style_args = dict(
    label_font_size=28,
    major_label_font_size=28,
    value_font_size=28,
    value_label_font_size=28,
    # tooltip_font_size=18,
    title_font_size=40,
    legend_font_size=34,
)

netdevops_style_trends = Style(colors=TRENDS_COLOR, **style_args)


def reorder_index_we_havent(indexes):

    tmp = list(indexes)

    # Identify if and where is the response "we haven't automated ..." and move it to the end
    we_haven_pos = None
    we_haven = None
    for i in range(0, len(tmp)):
        if "we haven" in tmp[i].lower() or "we are not" in tmp[i].lower():
            we_haven_pos = i
            we_haven = tmp[i]

    if we_haven_pos:
        del tmp[we_haven_pos]
        tmp.insert(0, we_haven)

    return tmp


def generate_graphs(
    chart, filename, out_dir="../results/graphs", out_format=["svg", "png"]
):
    """
    Generate images from chart object
    Support either PNG or SVG format
    """

    if "png" in out_format:
        chart.render_to_png(f"{out_dir}/{filename}.png")

    if "svg" in out_format:
        chart.render_to_file(f"{out_dir}/{filename}.svg")

    logging.info(f"Generated {filename} {out_format}")


def stacked_graph_gsq(session, sq, results_order=None):
    """
    Generate HorizontalStackedBar graphs 
    for a Survey Question of type `Multiple choice grid`

    if results_order is provided, the results will be display in this order 
    """

    results = get_gsq_results(session, sq, percentage=True)

    # convert index to lowercase to simplify mapping
    # Will convert it to Title just before rendering
    results.index = [idx.lower() for idx in results.index]

    # if results_order has been provided
    # First order the index based on the list provided
    # then order the columns by the value of the last element of the list
    if results_order:
        order_lower = [idx.lower() for idx in results_order]
        results = results.reindex(order_lower, axis=0)
        results = results.sort_values(by=order_lower[-1], axis=1)

    for c in results.columns:
        if "(" in c:
            results = results.rename(columns={c: c.split("(")[0]})

    title = sq.text.replace("?", "?\n")

    chart = pygal.HorizontalStackedBar(
        legend_at_bottom=True,
        stack_from_top=True,
        width=1920,
        height=1080,
        title=f"NetDevOps Survey ({sq.survey_id}) \n {title}",
        style=netdevops_style_trends,
    )

    chart.x_labels = map(str, results.columns)

    for idx in results.index:
        chart.add(idx.title().replace("Don'T", "don't"), list(results.loc[idx]))

    return chart


def pie_graph(session, sq):
    """
    Generate Simple Pie Chart for a given SurveyQuestions
    """

    results = get_sq_results(session, sq)

    title = sq.text.replace("?", "?\n")

    chart = pygal.Pie(
        legend_at_bottom=False,
        width=1920,
        height=1080,
        title=f"NetDevOps Survey ({sq.survey_id}) \n {title}",
        style=LightenStyle(
            GREEN, step=int(len(list(results.index)) * 1.5), **style_args
        ),
        inner_radius=0.4,
    )

    for index, row in results.sort_values(by=["value"], ascending=False).iterrows():
        chart.add(index, row["value"])

    return chart


def bar_graph_tools(session, sq, percentage=True):
    """
    Generate Bar graphs for tools related questions
     - Order by responses
     - Exclude responses with less than 2 responses
     - Put negative response at the end (We have not / We haven't)
     - Add stats about the avg number of responses
    """

    results = get_sq_results(session, sq, percentage=percentage, min_count=2)
    count, avg_r, min_r, max_r = get_sq_stats(session, sq)

    # indexes = list(results.index)

    indexes = reorder_index_we_havent(results.index)
    results = results.reindex(indexes)

    for index in indexes:
        if "we haven" in index.lower():
            results = results.rename(index={index: "We haven't automated .."})
        elif "we are not" in index.lower():
            results = results.rename(index={index: "We are not .."})
  
    if percentage:
        x_legend = "%"
    else:
        x_legend = "count"

    title = sq.text.replace("? ", "?\n")
    stats = f"Stats: {avg_r} avg, max {max_r} "

    chart = pygal.HorizontalBar(
        legend_at_bottom=False,
        width=1920,
        height=1080,
        title=f"NetDevOps Survey ({sq.survey_id})\n{title}\n{stats}",
        style=LightenStyle(GREEN, step=2, **style_args),
        x_title=x_legend,
    )

    chart.show_legend = False
    chart.x_labels = map(str, list(results.index))
    chart.add(sq.survey.id, list(results["value"]))

    return chart


def bar_graph(session, sq, percentage=True, sort=False):

    results = get_sq_results(session, sq, percentage=percentage, sort=sort)
    count, avg_r, min_r, max_r = get_sq_stats(session, sq)

    if percentage:
        x_legend = "%"
    else:
        x_legend = "count"

    title = sq.text.replace("?", "?\n")
    if sq.question.type == "Multiple choice":
        stats = f"Stats: {avg_r} avg, max {max_r}"
        chart_title = f"NetDevOps Survey ({sq.survey_id})\n{title}\n{stats}"
    else:
        chart_title = f"NetDevOps Survey ({sq.survey_id})\n{title}"

    chart = pygal.HorizontalBar(
        legend_at_bottom=False,
        width=1920,
        height=1080,
        title=chart_title,
        style=LightenStyle(GREEN, step=2, **style_args),
        x_title=x_legend,
    )

    chart.show_legend = False
    chart.x_labels = map(str, list(results.index))
    chart.add(sq.survey.id, list(results["value"]))

    return chart


def compare_results_over_time_hbar(session, q, results_order=None):

    results = get_q_results_over_time(session, q, percentage=True, min_count=2)

    ## Sort Index by mean values
    results = results.reindex(results.mean(1).sort_values(0).index, axis=0)

    ## Move We haven't / We are responses at the bottom
    indexes = reorder_index_we_havent(results.index)
    results = results.reindex(indexes)

    for index in indexes:
        if "we haven" in index.lower():
            results = results.rename(index={index: "We haven't automated .."})
        elif "we are not" in index.lower():
            results = results.rename(index={index: "We are not .."})
  

    title = q.desc.replace("?", "?\n")

    if q.parent_id:
        pq = session.query(Questions).get(q.parent_id)
        title = pq.desc + ": " + title

    chart = pygal.HorizontalBar(
        legend_at_bottom=False,
        width=1920,
        height=1080,
        title=f"NetDevOps Survey \n {title}",
        style=LightenStyle(
            GREEN, step=int(len(list(results.columns)) * 1.25), **style_args
        ),
        x_title="%",
    )
    chart.x_labels = map(str, list(results.index))

    for column in list(results.columns):
        chart.add(column, list(results[column]))

    return chart


def compare_results_over_time_sbar(session, q, results_order=None):
    """
    Generate a HorizontalStackedBar graph to compare results over time
    for a specific Multiple choice grid option
    """

    results = get_q_results_over_time(session, q, percentage=True, min_count=2)

    # convert index to lowercase to simplify mapping
    # Will convert it to Title just before rendering
    results.index = [idx.lower() for idx in results.index]

    # if results_order has been provided
    # First order the index based on the list provided
    # then order the columns by the value of the last element of the list
    if results_order:
        order_lower = [idx.lower() for idx in results_order]
        results = results.reindex(order_lower, axis=0)
        results = results.sort_values(by=order_lower[-1], axis=1)

    # order columns too
    cols = sorted(list(results.columns))
    results = results[cols]

    title = q.desc.replace("?", "?\n")

    if q.parent_id:
        pq = session.query(Questions).get(q.parent_id)
        title = pq.desc + ": " + title

    nbr_edition = len(list(results.columns))
    chart = pygal.HorizontalStackedBar(
        legend_at_bottom=True,
        stack_from_top=True,
        width=1920,
        height=320+nbr_edition*160,
        title=f"NetDevOps Survey \n {title}",
        style=netdevops_style_trends,
    )

    chart.x_labels = map(str, results.columns)

    for idx in results.index:
        chart.add(idx.title().replace("Don'T", "don't"), list(results.loc[idx]))

    return chart


def compare_results_nwk_size(session, sq):

    sq2 = (
        session.query(SurveyQuestions)
        .filter(SurveyQuestions.question_id == "env-nbr-devices")
        .filter(SurveyQuestions.survey_id == sq.survey_id)
        .first()
    )

    results = get_sq_results_group_by_sq(session, sq, sq2)
    results = results.fillna(0)

    # order columns by average value
    cols = {}
    for col in list(results.columns):
        nbrs = re.findall(r"\d+", col)
        nbrs = [int(i) for i in nbrs]
        cols[col] = sum(nbrs) / len(nbrs)

    results = results[sorted(cols.keys(), key=cols.get)]

    title = sq.text.replace("?", "?\n")

    chart = pygal.HorizontalBar(
        legend_at_bottom=False,
        width=1920,
        height=1080,
        title=f"NetDevOps Survey \n {title}",
        style=LightenStyle(
            RED, step=int(len(list(results.index)) * 1.25), **style_args
        ),
        x_title="%",
    )

    chart.x_labels = map(str, list(results.index))

    for column in list(results.columns):
        chart.add(column, list(results[column]))

    return chart
