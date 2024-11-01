from apscheduler.schedulers.blocking import BlockingScheduler

from utils.simple_utils import *
from utils.google_utils import *
from utils.langchain_utils import *
from utils.best_hashtags import *

from mongo.interface import *

from chroma_interface.reader import Reader
from chroma_interface.writer import Writer
from chroma_interface import *

from multiprocessing import Process, Pool

import multiprocessing
import os
import time
import pickle as pkl
import pandas as pd
import numpy as np
import json

sched = BlockingScheduler()


# Constants
NEWS_TOPICS = read_lines_from_file("./config/topic-type.txt")

COUNTRY_NAMES = read_lines_from_file("./config/countries-names.txt")
COUNTRY_CODES = defaultdict(None)
for name, code in zip(COUNTRY_NAMES, read_lines_from_file("./config/countries-code.txt")):
    COUNTRY_CODES[name] = code

COUNTRY_CODES_TO_NAMES = defaultdict(None)
for name, code in zip(COUNTRY_NAMES, read_lines_from_file("./config/countries-code.txt")):
    COUNTRY_CODES_TO_NAMES[code] = name

QUERY_KEYWORDS_DICT = json.load(open("./config/query-topics.json", 'r'))
QUERY_TOPICS = list(QUERY_KEYWORDS_DICT.keys())

QUERY_KEYWORDS = []
for item in QUERY_KEYWORDS_DICT.values():
    QUERY_KEYWORDS.extend(item)

def update_user_moments(user):
    global QUERY_TOPICS

    news_limit = int(os.environ["NEWS_DATA_LIMIT"])

    lang="en"

    company_id = user["company_id"]
    company_name = user["company_name"]
    company_description = user["company_description"]
    country = user["country"]
    country_code = user["country_code"]
    country = user["country"]
    content_category = user['content_category']

    print("updating", company_name)

    mongo_client = MongoInterface(
        url=os.environ["MONGO_CONNECTION_STRING"],
        database="users",
        collection="user-data"
    )


    chroma_reader, chroma_writer = get_reader_writer(
        host=os.environ["CHROMA_IP"],
        port=int(os.environ["CHROMA_PORT"]),
        openai_api_key=os.environ["OPENAI_API_KEY"]
    )

    # generate industry moments
    # 1: Create industry news moments
    collection_name = f"{company_id}_industry_news"

    chroma_reader.set_collection(collection_name)

    create_new_collection(chroma_reader, chroma_writer, collection_name)

    news_df = news_from_query(content_category + "|" + company_description, country=country_code, llm_name="gpt-3-openai")
    news_df = news_df[(news_df["top_image"] != "") & (news_df["keywords"] != "")]
    news_df["country_code"] = [country_code] * len(news_df)

    docs, metadata = load_df(news_df)

    chroma_writer.update(collection_name, docs, metadata)

    industry_news_moments = filter_news(content_category + "|" + company_description, chroma_reader)[:news_limit]

    # 2: Create social media moments
    collection_name = f"{company_id}_social_media"
    chroma_reader.set_collection(collection_name)
    create_new_collection(chroma_reader, chroma_writer, collection_name)

    relevant_links = googleSearch(
        content_category,
        country_code,
        num_results=20
    )

    articles = parse_multiple_news_urls(relevant_links)
    articles_data = [{"source": item.title, "text": item.text} for item in articles if item is not None]

    # split documents and create metadata for every document
    docs, metadata = build_splited_docs(articles_data)

    chroma_writer.update(collection_name, docs, metadata)

    social_media_moments = generate_social_media_trends(
        content_category=content_category,
        chroma_reader=chroma_reader,
    )

    # 3: Create general news moments
    collection_name = "general_news"
    chroma_reader.set_collection(collection_name)

    general_news_moments = filter_news(content_category + "|" + company_description, chroma_reader, country_code)[:news_limit]

    # 4: Current events moments
    collection_name = "current_events"

    chroma_reader.set_collection(collection_name)

    current_events_moments = generate_current_events(
        company_description=company_description, 
        chroma_reader=chroma_reader, 
        topic_list=QUERY_TOPICS, 
        keywords_dict=QUERY_KEYWORDS_DICT, 
        country_code=country_code,
        country=country)[:news_limit]

    print({
        "general_news": general_news_moments,
        "industry_news": industry_news_moments,
        "current_events": current_events_moments,
        "social_media_trends": social_media_moments
    })

    mongo_client.update_user_moments(company_id,{
        "General News": general_news_moments,
        "Industry News": industry_news_moments,
        "Current Events": current_events_moments,
        "social_media_trends": social_media_moments
    })

    return None


def prepare_news_data(data):
    topic, country_code = data

    lang="en"

    news_df = get_news_by_topic(topic, country=country_code, lang=lang)
    
    # Simple filter for where image or keywords do not exist
    news_df = news_df[(news_df["top_image"] != "") & (news_df["keywords"] != "")]
    news_df["country_code"] = [country_code] * len(news_df)

    # parse dataframe into documents and metadata
    documents, metadata = load_df(news_df)

    return documents, metadata

def get_general_news_data():
    global COUNTRY_CODES, NEWS_TOPICS

    num_workers = int(os.environ["NUM_WORKERS"])

    collection_name = "general_news"
    lang="en"

    chroma_reader, chroma_writer = get_reader_writer(
        host=os.environ["CHROMA_IP"],
        port=int(os.environ["CHROMA_PORT"]),
        openai_api_key=os.environ["OPENAI_API_KEY"],
        reader_collection_name=collection_name
    )

    create_new_collection(chroma_reader, chroma_writer, collection_name)

    with Pool(num_workers) as pool:
        for country_name, country_code in COUNTRY_CODES.items():
            print("Gathering data for", country_name, country_code)

            docs_and_meta = pool.map(prepare_news_data, [(topic, country_code) for topic in NEWS_TOPICS])

            documents = []
            metadata = []

            for d, m in docs_and_meta:
                documents.extend(d)
                metadata.extend(m)

            # # get data from google news about the topic
            # news_df = get_news_by_topic(topic, country=country_code, lang=lang)

            # # Simple filter for where image or keywords do not exist
            # news_df = news_df[(news_df["top_image"] != "") & (news_df["keywords"] != "")]
            # news_df["country_code"] = [country_code] * len(news_df)

            # # parse dataframe into documents and metadata
            # documents, metadata = load_df(news_df)

            # embed and push vectors to chroma
            chroma_reader, chroma_writer = get_reader_writer(
                host=os.environ["CHROMA_IP"],
                port=int(os.environ["CHROMA_PORT"]),
                openai_api_key=os.environ["OPENAI_API_KEY"],
                reader_collection_name=collection_name
            )
            chroma_writer.update(collection_name, documents, metadata)

def prepare_events_data(data):
    topic, target, country_code = data
    
    news_df = get_news_by_search(f"upcoming or ongoing major events about {topic}", limit=50, country=country_code)

    # Simple filter for where text does not exist
    news_df = news_df[(news_df[target].isna() == False)]
    news_df["country_code"] = [country_code] * len(news_df)

    # parse dataframe into documents and metadata
    news_df["country_code"] = [country_code] * len(news_df)
    documents, metadata = split_df(news_df, target)

    # embed and push vectors to chroma
    return documents, metadata

def get_current_events():
    global QUERY_TOPICS, COUNTRY_CODES

    num_workers = int(os.environ["NUM_WORKERS"])
    collection_name = "current_events"
    target = "text"

    chroma_reader, chroma_writer = get_reader_writer(
        host=os.environ["CHROMA_IP"],
        port=int(os.environ["CHROMA_PORT"]),
        openai_api_key=os.environ["OPENAI_API_KEY"],
        reader_collection_name=collection_name
    )

    create_new_collection(chroma_reader, chroma_writer, collection_name)

    # for every country in the configuration run data extraction on all topics
    with Pool(num_workers) as pool:
        for country_name, country_code in COUNTRY_CODES.items():
            
            docs_and_meta = pool.map(prepare_events_data, [(topic, target, country_code) for topic in QUERY_TOPICS])

            # get links for all the topics
            documents = []
            metadata = []

            for d, m in docs_and_meta:
                documents.extend(d)
                metadata.extend(m)

            # embed and push vectors to chroma
            chroma_writer.update(collection_name, documents, metadata)


@sched.scheduled_job('cron', second="0", minute="0", hour="*/6", month="*", day="*", year="*")
def job():
    # connect to MongoDB endpoint
    user_mongo_client = MongoInterface(
        url=os.environ["MONGO_CONNECTION_STRING"],
        database="users",
        collection="user-data"
    )

    # Common data, General news and current affairs
    # 1: General Dataset extraction

    # Start a branching process for general news extraction
    print("Starting general news extraction process")
    general_news_process = Process(target=get_general_news_data, args=())
    general_news_process.start()

    # 2: Current events
    print("Starting current events extraction process")
    get_current_events()
    
    # Wait for both processes to finish before proceeding
    general_news_process.join()

    print("Updating user moments")
    # Create personalized industry news for every user
    userlist = user_mongo_client.get_user_list()

    with Pool(1) as pool:
        [item for item in pool.imap(update_user_moments, userlist)]

if __name__ == "__main__":
    try:
        # environment setup
        with open(".env", "r") as key_file:
            keys = list(key_file)

        for item in keys:
            variable, value = item.split("=")[0], "=".join(item.split("=")[1:])
            os.environ[variable] = value.replace("\n", "")
    except:
        print("no .env file found")

        if "CHROMA_IP" in os.environ:
            print("environment seems to be updated")
        else:
            print("Environment not setup properly")
            exit(1)

    job()
    
    # sched.start()