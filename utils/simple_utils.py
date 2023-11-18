# from googlesearch import search
from newspaper import Article
from googleapiclient.discovery import build
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import date
from urllib.parse import urlparse
from pprint import pprint
from pygooglenews import GoogleNews
from collections import defaultdict
from newspaper import Article

import newspaper
import requests
import pandas as pd


def divide_chunks(l, n):
    for i in range(0, len(l), n): 
        yield l[i:i + n]


def extract_text_from(url):
    print("Getting text:", url)
    html = requests.get(url, headers={"user-agent": "something"}).text
    soup = BeautifulSoup(html, features="html.parser")
    text = soup.get_text()

    lines = (line.strip() for line in text.splitlines())
    return '\n'.join(line for line in lines if line)

def extract_all_links(url):
    print("Getting links:", url)
    hostname = urlparse(url).hostname
    reqs = requests.get(url, headers={"user-agent": "something"})
    soup = BeautifulSoup(reqs.text, 'html.parser')
    links = []
    for element in soup.find_all('a'):
        link = element.get('href')
        link_hostname = urlparse(link).hostname

        if link_hostname == hostname:
            links.append(link)

    return links

def get_sitetexts(sitelinks):
    """extract text from a list of given sites"""
    sitetexts = []
    for url in sitelinks:
        try:
            text = extract_text_from(url)

            text = " ".join(text.split(" ")[:1000])

            sitetexts.append({
                "source": url,
                "text": text
            })
        except:
            pass

    return sitetexts


def scrape_sites(urls, limit=2):
    temp = []

    for url in urls:
        try:
            temp.extend(extract_all_links(url))
        except:
            pass

        if len(temp) >= limit:
            temp = temp[:limit+1]
            break

    urls = pd.Series(urls + temp).unique()
    sitetexts = get_sitetexts(urls)

    return sitetexts


def current_date():
    """
    Returns current date in yyyy-mm-dd format

    Returns:
    - str
    """
    return str(date.today())

def read_lines_from_file(path):
    """
    reads lines from a filepath and returns everything in a list

    Params:
    - path: str

    Returns:
    - List
    """
    return open(path, 'r').read().split("\n")

# ---------------NEWSPAPER UTILS--------------
def parse_news_url(url:str)->Article:
    """
    Parse the article for the given URL and convert them to newspaper3k.Article object

    dependencies: newpaper3k.Article

    Args:
        - url = str containing the urls of Articles
    Returns:
        - Artcile Objects

    Raises:
        - newspaper.ArticleException
    """
    try:
        article = Article(url=url)
        article.download()
        article.parse()

        return article
    
    except newspaper.ArticleException as e:

        return None

def parse_for_current_events(_in)->dict:
    url, country_code = _in
    article = parse_news_url(url)

    if not article:
        return None
    
    return {
            "source": article.title, 
            "text": article.text,
            "country_code": country_code}

def parse_multiple_news_urls(urls:list)->list[Article]:
    """
    Parse the articles for the given URL and convert them to newspaper3k.Article object

    dependencies: newpaper3k.Article

    Args:
        - urls = List of str containing the urls of Articles
    Returns:
        - List of Artcile Objects
    """
    articles = []

    for item in urls:
        article = parse_news_url(item)

        if article:
            articles.append(article)
    
    return tuple(articles)

def process_data(data):
    if data[0] == []:
        data = data[1:]

    for i in range(len(data)):
        data[i][2] = int(data[i][2].replace(",", ""))

    return_dict = {}
    for i in range(len(data)):
        return_dict[data[i][1]] = return_dict[i][2]
    return return_dict

def best_hashtag_get_popular(query:str):
    """
    Scrape popular hashtags from best hashtags

    Args:
        query:str, query to search hash tags
    
    Return:
        dict[list]= keys = [table,hashtags]

    """
    print("[GET] Popular hashtags")
    query= query.lower()
    query = query.replace(" ", "")
    try:
        url = f"http://best-hashtags.com/hashtag/{query}"
    except Exception as e:
        print("[FAILED] Popular hashtags")
        return {"hashtags":[],"table":[]}
    
    resp = requests.get(url)
    soup = bs4.BeautifulSoup(resp.text,"lxml")
    popualr = soup.find("div",dict(id="popular"))
    if popualr is None:
        print("No data in popular")
        return []

    data = []
    rows = popualr.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele])
    
    return process_data(data)

def get_best_hashtags_data(hashtag:str) -> dict[dict]:
    pass