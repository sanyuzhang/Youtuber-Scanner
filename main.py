"""
This module implements a (partial, sample) query interface for elasticsearch movie search. 
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
from index import Movie
from pprint import pprint
from constants import STOPWORDS
from elasticsearch_dsl import Q
from elasticsearch_dsl.utils import AttrList
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

app = Flask(__name__)

# Initialize global variables for rendering page
tmp_text = ""
tmp_title = ""
tmp_language = ""
tmp_country = ""
tmp_director = ""
tmp_location = ""
tmp_time = ""
tmp_categories = ""
tmp_star = ""
tmp_min = ""
tmp_max = ""
gresults = {}

# display query page
@app.route("/")
def search():
    return render_template('page_query.html')

# display results page for first set of results and "next" sets.
@app.route("/results", defaults={'page': 1}, methods=['GET', 'POST'])
@app.route("/results/<page>", methods=['GET', 'POST'])
def results(page):
    global tmp_text
    global tmp_title
    global tmp_language
    global tmp_country
    global tmp_director
    global tmp_location
    global tmp_time
    global tmp_categories
    global tmp_star
    global tmp_min
    global tmp_max
    global gresults

    # convert the <page> parameter in url to integer.
    if type(page) is not int:
        page = int(page.encode('utf-8'))
    # if the method of request is post (for initial query), store query in local global variables
    # if the method of request is get (for "next" results), extract query contents from client's global variables
    if request.method == 'POST':
        text_query = request.form['query']
        star_query = request.form['starring']
        language_query = request.form['language']
        country_query = request.form['country']
        director_query = request.form['director']
        location_query = request.form['location']
        time_query = request.form['time']
        categories_query = request.form['categories']
        mintime_query = request.form['mintime']
        if len(mintime_query) is 0:
            mintime = 0
        else:
            mintime = int(mintime_query)
        maxtime_query = request.form['maxtime']
        if len(maxtime_query) is 0:
            maxtime = 99999
        else:
            maxtime = int(maxtime_query)

        # update global variable template data
        tmp_text = text_query
        tmp_language = language_query
        tmp_country = country_query
        tmp_director = director_query
        tmp_location = location_query
        tmp_time = time_query
        tmp_categories = categories_query
        tmp_star = star_query
        tmp_min = mintime
        tmp_max = maxtime
    else:
        # use the current values stored in global variables.
        text_query = tmp_text
        language_query = tmp_language
        country_query = tmp_country
        director_query = tmp_director
        location_query = tmp_location
        time_query = tmp_time
        categories_query = tmp_categories
        star_query = tmp_star
        mintime = tmp_min
        if tmp_min > 0:
            mintime_query = tmp_min
        else:
            mintime_query = ""
        maxtime = tmp_max
        if tmp_max < 99999:
            maxtime_query = tmp_max
        else:
            maxtime_query = ""

    ignored = {}
    # store query values to display in search boxes in UI
    shows = {}
    shows['text'] = text_query
    shows['language'] = language_query
    shows['country'] = country_query
    shows['director'] = director_query
    shows['location'] = location_query
    shows['time'] = time_query
    shows['categories'] = categories_query
    shows['starring'] = star_query
    shows['maxtime'] = maxtime_query
    shows['mintime'] = mintime_query

    # Create a search object to query our index
    search = Search(index='sample_film_index')

    # Build up your elasticsearch query in piecemeal fashion based on the user's parameters passed in.
    # The search API is "chainable".
    # Each call to search.query method adds criteria to our growing elasticsearch query.
    # You will change this section based on how you want to process the query data input into your interface.

    not_found = False
    unknown_runtime, unknown_text, unknown_language, unknown_country, unknown_director, unknown_star, unknown_location, unknown_time, unknown_category = '', '', '', '', '', '', '', '', ''

    # search for runtime using a range query
    s = search.query('range', runtime={'gte': mintime, 'lte': maxtime})
    if s.count() == 0:
        not_found = True
        unknown_runtime = str(mintime) + ' ~ ' + str(maxtime)
    
    # search for text
    if not_found is False:
        if len(text_query) > 0:
            # search terms
            terms = re.sub('["].*?["]', "", text_query).lower().strip().split()
            ignored = {t for t in terms if t in STOPWORDS}
            terms = [t for t in terms if t not in STOPWORDS]
            for t in terms:
                s = s.query(Q("multi_match", query=t, fields=['title'], type='most_fields', boost=10) | Q(
                    "multi_match", query=t, fields=['text'], type='most_fields', boost=1))
                if s.count() == 0:
                    not_found = True
                    unknown_text = t
                    break
            
            # search phrases
            if not_found is False:
                phrases = re.findall(r'"(.*?)"', text_query)
                for p in phrases:
                    s = s.query(Q("multi_match", query=p.lower(), fields=['title'], type='phrase', boost=10) | Q(
                        "multi_match", query=p.lower(), fields=['text'], type='phrase', boost=1))
                    if s.count() == 0:
                        not_found = True
                        unknown_text = p
                        break
                    
    # search for language
    if not_found is False:
        if len(language_query) > 0:
            for l in language_query.split():
                s = s.query('match', language=l.lower())
                if s.count() == 0:
                    not_found = True
                    unknown_language = l
                    break

    # search for country
    if not_found is False:
        if len(country_query) > 0:
            for c in country_query.split():
                s = s.query('match', country=c.lower())
                if s.count() == 0:
                    not_found = True
                    unknown_country = c
                    break
    

    # search for director
    if not_found is False:
        if len(director_query) > 0:
            for d in director_query.split():
                s = s.query('match', director=d.lower())
                if s.count() == 0:
                    not_found = True
                    unknown_director = d
                    break
    
    # search for starring
    if not_found is False:
        if len(star_query) > 0:
            for star in star_query.split():
                s = s.query('match', starring=star.lower())
                if s.count() == 0:
                    not_found = True
                    unknown_star = star
                    break

    # search for location
    if not_found is False:
        if len(location_query) > 0:
            for l in location_query.split():
                s = s.query('match', location=l.lower())
                if s.count() == 0:
                    not_found = True
                    unknown_location = l
                    break
    
    # search for time
    if not_found is False:
        if len(time_query) > 0:
            for t in time_query.split():
                s = s.query('match', time=t)
                if s.count() == 0:
                    not_found = True
                    unknown_time = t
                    break
    
    # search for categories
    if not_found is False:
        if len(categories_query) > 0:
            for c in categories_query.split():
                s = s.query('match', categories=c.lower())
                if s.count() == 0:
                    not_found = True
                    unknown_category = c
                    break

    # highlight
    s = s.highlight_options(pre_tags='<mark>', post_tags='</mark>')
    s = s.highlight('text', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('title', fragment_size=999999999, number_of_fragments=1)

    # determine the subset of results to display (based on current <page> value)
    start = 0 + (page - 1) * 10
    end = 10 + (page - 1) * 10

    # execute search and return results in specified range.
    response = s[start:end].execute()

    # insert data into response
    resultList = {}
    for hit in response.hits:
        result = {}
        result['score'] = hit.meta.score

        if 'highlight' in hit.meta:
            if 'title' in hit.meta.highlight:
                result['title'] = hit.meta.highlight.title[0]
            else:
                result['title'] = hit.title

            if 'text' in hit.meta.highlight:
                result['text'] = hit.meta.highlight.text[0]
            else:
                result['text'] = hit.text

        else:
            result['title'] = hit.title
            result['text'] = hit.text
        resultList[hit.meta.id] = result

    # make the result list available globally
    gresults = resultList

    # get the total number of matching results
    result_num = response.hits.total

    # if we find the results, extract title and text information from doc_data, else do nothing
    if result_num > 0:
        return render_template('page_SERP.html', results=resultList, res_num=result_num, page_num=page, queries=shows, stop_len=len(ignored), ignored=ignored)
    else:
        message = []
        if len(unknown_runtime) > 0:
            message.append('Cannot find runtime between: ' + unknown_runtime)
        if len(unknown_text) > 0:
            message.append('Unknown search term: ' + unknown_text)
        if len(unknown_language) > 0:
            message.append('Cannot find language: ' + unknown_language)
        if len(unknown_country) > 0:
            message.append('Cannot find country: ' + unknown_country)
        if len(unknown_director) > 0:
            message.append('Cannot find director: ' + unknown_director)
        if len(unknown_star) > 0:
            message.append('Cannot find star: ' + unknown_star)
        if len(unknown_location) > 0:
            message.append('Cannot find location: ' + unknown_location)
        if len(unknown_time) > 0:
            message.append('Cannot find time: ' + unknown_time)
        if len(unknown_category) > 0:
            message.append('Cannot find category: ' + unknown_category)

        return render_template('page_SERP.html', results=message, res_num=result_num, page_num=page, queries=shows, stop_len=len(ignored), ignored=ignored)

# display a particular document given a result number
@app.route("/documents/<res>", methods=['GET'])
def documents(res):
    global gresults
    film = gresults[res]
    filmtitle = film['title']
    for term in film:
        if type(film[term]) is AttrList:
            s = "\n"
            for item in film[term]:
                s += item + ",\n "
            film[term] = s
    # fetch the movie from the elasticsearch index using its id
    movie = Movie.get(id=res, index='sample_film_index')
    filmdic = movie.to_dict()
    film['runtime'] = str(filmdic['runtime']) + " min"
    return render_template('page_targetArticle.html', film=film, title=filmtitle)


if __name__ == "__main__":
    app.run()
