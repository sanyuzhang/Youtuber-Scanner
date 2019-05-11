"""
This module implements a (partial, sample) query interface for elasticsearch channel search. 
You will need to rewrite and expand sections to support the types of queries over the fields in your UI.

Documentation for elasticsearch query DSL:
https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html

For python version of DSL:
https://elasticsearch-dsl.readthedocs.io/en/latest/

Search DSL:
https://elasticsearch-dsl.readthedocs.io/en/latest/search_dsl.html
"""

import re
from flask import *
from index import Channel
from pprint import pprint
from constants import STOPWORDS
from elasticsearch_dsl import Q
from elasticsearch_dsl.utils import AttrList
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

app = Flask(__name__)

# Initialize global variables for rendering page
orig_query = ""
orig_channel_title = ""
orig_upload_interval = ""
gresults = {}

# display query page
@app.route("/")
def search():
    return render_template('index.html')

# display results page for first set of results and "next" sets.
@app.route("/results", methods=['POST'])
def results():
    global orig_query
    global orig_channel_title
    global orig_upload_interval
    global gresults

    page_id = get_page_id(request)

    # if the method of request is post (for initial query), store query in local global variables
    # if the method of request is get (for "next" results), extract query contents from client's global variables
    query = request.form['query']
    channel_title = request.form['channel_title']
    upload_interval = request.form['upload_interval']

    # update global variable template data
    orig_query = query
    orig_channel_title = channel_title
    orig_upload_interval = upload_interval

    ignored = {}

    # Create a search object to query our index
    search = Search(index='channel_index')

    # Build up your elasticsearch query in piecemeal fashion based on the user's parameters passed in.
    # The search API is "chainable".
    # Each call to search.query method adds criteria to our growing elasticsearch query.
    # You will change this section based on how you want to process the query data input into your interface.
    not_found = False
    unknown_query, unknown_channel_title, unknown_upload_interval = '', '', ''

    # search for text
    terms = re.sub('["].*?["]', "", query).lower().strip().split()
    ignored = {t for t in terms if t in STOPWORDS}
    terms = [t for t in terms if t not in STOPWORDS]
    for t in terms:
        s = search.query(Q("multi_match", query=t, fields=['channel_title'], type='most_fields', boost=10)
                         | Q("multi_match", query=t, fields=['channel_desc'], type='most_fields', boost=9)
                         | Q("multi_match", query=t, fields=['all_playlists_titles'], type='most_fields', boost=6)
                         | Q("multi_match", query=t, fields=['all_playlists_desc'], type='most_fields', boost=5)
                         | Q("multi_match", query=t, fields=['all_videos_titles'], type='most_fields', boost=2)
                         | Q("multi_match", query=t, fields=['all_videos_desc'], type='most_fields', boost=1))
        if s.count() == 0:
            not_found = True
            unknown_query = t
            break

    # search phrases
    if not_found is False:
        phrases = re.findall(r'"(.*?)"', query)
        for p in phrases:
            s = s.query(Q("multi_match", query=p.lower(), fields=['title'], type='phrase', boost=10)
                        | Q("multi_match", query=p.lower(), fields=['channel_desc'], type='most_fields', boost=9)
                        | Q("multi_match", query=p.lower(), fields=['all_playlists_titles'], type='most_fields', boost=6)
                        | Q("multi_match", query=p.lower(), fields=['all_playlists_desc'], type='most_fields', boost=5)
                        | Q("multi_match", query=p.lower(), fields=['all_videos_titles'], type='most_fields', boost=2)
                        | Q("multi_match", query=p.lower(), fields=['all_videos_desc'], type='most_fields', boost=1))
            if s.count() == 0:
                not_found = True
                unknown_query = p
                break

    # search for youtuber's name
    if not_found is False:
        if len(channel_title) > 0:
            for t in channel_title.split():
                term = '*' + t.lower() + '*'
                s = s.query('wildcard', channel_title=term)
                if s.count() == 0:
                    not_found = True
                    unknown_channel_title = t
                    break

    # search for upload frequency
    if not_found is False:
        if len(upload_interval) > 0:
            s = s.query('range', upload_interval={
                        'lte': float(upload_interval)})
            if s.count() == 0:
                not_found = True
                unknown_upload_interval = upload_interval

    # determine the subset of results to display (based on current <page_id> value)
    start = 0 + (page_id - 1) * 10
    end = 10 + (page_id - 1) * 10

    # execute search and return results in specified range.
    response = s[start:end].execute()

    # insert data into response
    result_list = {}
    for hit in response.hits:
        result = hit
        result['score'] = hit.meta.score
        result['upload_interval'] = round(hit.upload_interval, 1)
        result_list[hit.meta.id] = result

    # make the result list available globally
    gresults = result_list

    # get the total number of matching results
    result_num = response.hits.total

    # if we find the results, extract title and text information from doc_data, else do nothing
    if result_num > 0:
        return render_template('index.html', is_result=True, results=result_list, res_num=result_num, pages_num=int(result_num / 10 + 1), page_id=page_id, orig_query=query, orig_channel_title=channel_title, orig_upload_interval=upload_interval, ignored=ignored)
    else:
        message = []
        if len(unknown_query) > 0:
            message.append('Unknown keyword: ' + unknown_query)
        if len(unknown_channel_title) > 0:
            message.append('Unknown youtuber: ' + unknown_channel_title)
        if len(unknown_upload_interval) > 0:
            message.append(
                'Cannot find youtubers uploading video every %d days' % unknown_channel_title)

        return render_template('index.html', is_result=True, results=message, res_num=0, pages_num=0, page_id_id=0, orig_query=query, orig_channel_title=channel_title, orig_upload_interval=upload_interval, ignored=ignored)


# display a particular document given a result number
@app.route("/documents/<res>", methods=['GET'])
def documents(res):
    global gresults
    channel = gresults[res]
    channel_title = channel['channel_title']
    for term in channel:
        if type(channel[term]) is AttrList:
            s = "\n"
            for item in channel[term]:
                s += item + ",\n "
            channel[term] = s
    # fetch the channel from the elasticsearch index using its id
    ch = Channel.get(id=res, index='channel_index')
    channel_dict = ch.to_dict()
    channel['upload_interval'] = str(channel_dict['upload_interval']) + " days"
    return render_template('detail.html', channel=channel, title=channel_title)


def get_page_id(request):
    """
    Return the current selected page id.
    """
    if 'page_id' in request.form:
        return int(request.form['page_id'])
    return request.args.get('page_id', default=1, type=int)


if __name__ == "__main__":
    app.run()
