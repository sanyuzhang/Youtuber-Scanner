# Youtuber-Scanner

A search engine that helps users find the most relevant youtube creator based on the users' queries.

Team member: Daniel Zhang, He Zhang, Shangyu Zhang(Team Leader)

Links:
* [Presentation1](https://docs.google.com/presentation/d/1GX61ccG3XShJF-RaaorWcl0rJkzyEUTFnD975_GIYQk/edit?usp=sharing)

## Design

This project involves 2 parts: a web UI and a backend.

The web UI will parse users' queries, then trigger correct intent, which will then handled by backend, generating proper response.

## How to use

This project involves 2 parts: Alexa Skill and a backend

### Backend Setups

#### Install Dependency

```bash
# install virtualenv to easily manage python versions
pip install virtualenv 

# Create your own ENV like
virtualenv ENV

# Source your ENV
source ENV\bin\activate

# Install packages by typing
pip install -r requirements.txt
```

#### Run

To run backend:
1. Enable the correct python virtual env
2. Start Elastic Search Server
2. `python backend/main.py`

A flask server will run on port 5555.
