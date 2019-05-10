import json
import re
import time
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch_dsl import Index, Document, Text, Keyword, Integer
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import tokenizer, analyzer
from elasticsearch_dsl.query import MultiMatch, Match


# Connect to local host server
connections.create_connection(hosts=['127.0.0.1'])

# Create elasticsearch object
es = Elasticsearch()

# Define analyzers appropriate for your data.
text_analyzer = analyzer(
    'custom',
    tokenizer='lowercase',
    filter=['stop', 'asciifolding']
)

name_analyzer = analyzer(
    'custom',
    tokenizer='standard',
    filter=['lowercase', 'asciifolding']
)

# Define document mapping (schema) by defining a class as a subclass of Document.
# This defines fields and their properties (type and analysis applied).
# You can use existing es analyzers or use ones you define yourself as above.


class Movie(Document):
    title = Text(analyzer=text_analyzer)
    text = Text(analyzer=text_analyzer)
    language = Text(analyzer=name_analyzer)
    country = Text(analyzer=name_analyzer)
    director = Text(analyzer=name_analyzer)
    location = Text(analyzer=name_analyzer)
    starring = Text(analyzer=name_analyzer)
    time = Text(analyzer=text_analyzer)
    runtime = Integer()
    categories = Text(analyzer=text_analyzer)

    # override the Document save method to include subclass field definitions
    def save(self, *args, **kwargs):
        return super(Movie, self).save(*args, **kwargs)

# Populate the index


def buildIndex():
    """
    buildIndex creates a new film index, deleting any existing index of
    the same name.
    It loads a json file containing the movie corpus and does bulk loading
    using a generator function.
    """
    film_index = Index('sample_film_index')
    if film_index.exists():
        film_index.delete()  # Overwrite any previous version
    film_index.document(Movie)
    film_index.create()

    # Open the json film corpus
    with open('films_corpus.json', 'r', encoding='utf-8') as data_file:
        # load movies from json file into dictionary
        movies = json.load(data_file)
        size = len(movies)

    # Action series for bulk loading with helpers.bulk function.
    # Implemented as a generator, to return one movie with each call.
    # Note that we include the index name here.
    # The Document type is always 'doc'.
    # Every item to be indexed must have a unique key.
    def actions():
        # mid is movie id (used as key into movies dictionary)
        for mid in range(1, size + 1):
            id = str(mid)
            yield {
                "_index": "sample_film_index",
                "_type": 'doc',
                "_id": mid,
                "title": movies[id]['Title'],
                "text": movies[id]['Text'],
                "language": movies[id]['Language'],
                "country": movies[id]['Country'],
                "director": movies[id]['Director'],
                "location": movies[id]['Location'],
                "starring": movies[id]['Starring'],
                "time": movies[id]['Time'],
                "runtime": getRuntimeInMin(movies[id]['Running Time']),
                "categories": movies[id]['Categories']
            }
    helpers.bulk(es, actions())


def getRuntimeInMin(runtime):
    # movies[str(mid)]['runtime'] # You would like to convert runtime to integer (in minutes)
    if type(runtime) is int:
        return runtime
    else:
        return 0

# command line invocation builds index and prints the running time.


def main():
    start_time = time.time()
    buildIndex()
    print("=== Built index in %s seconds ===" % (time.time() - start_time))


if __name__ == '__main__':
    main()
