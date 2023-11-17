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


import os
import pandas as pd


def get_metadata(article:Article) -> tuple[str,str,str,str]:
    img_url, keywords, card_text, description = "", "", "", ""

    try:
        img_url = article.top_image
    except:
        pass
    
    try:
        keywords = ",".join(article.meta_keywords)
    except:
        pass
    
    try:
        card_text = " ".join(article.text.split()[:20]) + "..."
    except:
        pass

    try:
        description = article.meta_description
    except:
        pass

    return img_url, keywords, card_text, description 
    


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
        
        try:
            article = parse_news_url(item["link"])
            img_url, keywords, card_text, description = get_metadata(article)
        except:
            pass

        news_headlines = pd.concat([
            news_headlines,
            pd.DataFrame({
                'title': item['title'],
                "description": description,
                'url': item['link'],
                'source_href': item["source"]["href"],
                'source': item['source']['title'],
                'top_image': img_url,
                'keywords': keywords,
                "card_text": card_text,
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
        img_url, keywords, card_text = "", "", ""
        
        try:
            article = parse_news_url(item["link"])
            img_url, keywords, card_text, description = get_metadata(article)
        except:
            pass

        news_headlines = pd.concat([
            news_headlines,
            pd.DataFrame({
                'title': item['title'],
                "description": description,
                'url': item['link'],
                'source_href': item["source"]["href"],
                'source': item['source']['title'],
                'top_image': img_url,
                'keywords': keywords,
                "card_text": card_text,
            }, index=[i])
        ])
    
    return news_headlines


def googleSearch(query:str, country:str="IN", num_results:int=10):
    """
    Fetches top 'n' links for the corresponding links  and 'query'

    Dependencies: pygoogle

    ! MUST HAVE "GOOGLE API KEY and SEARCH ENGINE KEY" as ENVIRONMENT VARIABLE
    Args:
        - query: string, the query to search on the internet
        - n    : int, number of links to return
    Returns:
        - List[Str]: List of string containing the URL of websites
    """
    #define key
    api_key = os.environ['GOOGLE_API_KEY']          # enviroment variable with API key
    cse_key = os.environ['SEARCH_ENGINE_KEY']       # enviroment variable with Search Engine Key
    
    results = []
    nextPage = 0
    n = num_results
    print("Getting information on:", query)

    # build the service
    resource = build("customsearch", 'v1', developerKey=api_key).cse()
    
    # search the required number of URLs
    for i in range(n//10):
        resp= resource.list(q=query, cx=cse_key,num=10,start=nextPage,gl=country,dateRestrict = {'d':30}).execute()
        nextPage = resp['queries']['nextPage'][0]['startIndex']
        links = [i['link'] for i in resp['items']]
        results.extend(links)
    resp = resource.list(q=query, cx=cse_key,num=n%10).execute()
    nextPage = resp['queries']['nextPage'][0]['startIndex']
    links = [i['link'] for i in resp['items']]
    results.extend(links[:n%10])
    
    # return the URLs
    return results
