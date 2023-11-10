from googlesearch import search
from newspaper import Article
from googleapiclient.discovery import build
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import date
from urllib.parse import urlparse
from pprint import pprint
from pygooglenews import GoogleNews
from collections import defaultdict


from .simple_utils import *


import pandas as pd


# ----------------- GOOGLE NEWS --------------------
def get_news_by_topic(topic, country="US", lang="en", limit=70):
    """
    Returns a pd.DataFrame object containing news data from Google News based on a TOPIC

    Params:
    - topic (required): str
    - country: str
    - lang: str
    - limit: int

    Returns:
    pd.DataFrame
    """
    news_headlines = pd.DataFrame()

    gn = GoogleNews(lang=lang, country=country)
    topic_heads = gn.topic_headlines(topic)

    for i, item in enumerate(tqdm(topic_heads["entries"][:limit+1], f"Getting headlines for {topic}")):
        news_headlines = pd.concat([
            news_headlines,
            pd.DataFrame({
                'title': item['title'],
                'link': item['link'],
                'source href': item["source"]["href"],
                'source name': item['source']['title'],
                'topic': topic
            }, index=[i])
        ])

    return news_headlines

def get_news_by_search(query, country="US", lang='en', limit=50):
    """
    Returns a pd.DataFrame object containing news data from Google News based on a search query

    Params:
    - topic (required): str
    - country: str
    - lang: str
    - limit: int

    Returns:
    pd.DataFrame

    """
    news_headlines = pd.DataFrame()

    gn = GoogleNews(lang=lang, country=country)
    topic_heads = gn.search(query)

    for i, item in enumerate(tqdm(topic_heads["entries"][:limit+1], f"Getting headlines for {query}")):
        news_headlines = pd.concat([
            news_headlines,
            pd.DataFrame({
                'title': item['title'],
                'link': item['link'],
                'source href': item["source"]["href"],
                'source name': item['source']['title']
            }, index=[i])
        ])
    
    return news_headlines