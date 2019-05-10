#coding = utf-8

from urllib.request import urlopen
import json
from bs4 import BeautifulSoup

import requests
import re

resSet = set([])

def getHtml(url):

    with urlopen(url) as page:
        html = requests.get(url)
        html.encoding = 'utf-8'
    return html.text

def parse(raw_text):
    pattern = re.compile(r"channelId")
    res = pattern.findall(raw_text)
    return res

def dfs(url, depth):
    if(depth == 0):
        return
    raw = getHtml(url)


raw = getHtml("https://www.youtube.com/channel/UCX9chJwW7gL93LIcC3xP2uQ")
print (raw)
print('\n')
print((parse(raw)))

