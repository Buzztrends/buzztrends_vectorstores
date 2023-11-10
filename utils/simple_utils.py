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
from newspaper import Article

import newspaper
import requests
import pandas as pd

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
    article = Article(url=url)
    article.download()
    article.parse()

    return article

def parse_articles(urls:list)->list[Article]:
    """
    Parse the articles for the given URL and convert them to newspaper3k.Article object

    dependencies: newpaper3k.Article

    Args:
        - urls = List of str containing the urls of Articles
    Returns:
        - List of Artcile Objects
    """
    articles = []
    for i,url in enumerate(urls):
        try:
            article = parse_news_url(url)
            print("GET:", url)
            articles.append(article)
        except newspaper.ArticleException as e:
            print("FAIL:", url)
    
    return tuple(articles)