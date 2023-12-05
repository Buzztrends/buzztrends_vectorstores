# langchain imports
import langchain
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain, RetrievalQA, ConversationalRetrievalChain, VectorDBQA, ChatVectorDBChain
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.memory.vectorstore import VectorStoreRetrieverMemory
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders import DataFrameLoader


import pandas as pd 
import openai
import json
import re

from .simple_utils import *
from .google_utils import *
from .best_hashtags import *
from .api_ninjas import *

from chroma_interface.reader import *
from chroma_interface.writer import *
from chroma_interface import *



MODELS = json.load(open("./config/openai-models.json", 'r'))

# ------------DOCUMENT INTERACTIONS---------------------
def load_df(df, page_content_column="title"):
    data = DataFrameLoader(df, page_content_column=page_content_column).load()

    documents = [item.page_content for item in data]
    metadata = [item.metadata for item in data]
    
    return documents, metadata


def build_splited_docs(sitetexts: list[dict], target_key:str="text"):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0, separators=[" ", ".", ",", "\n"])

    docs, metadatas = [], []
    for page in sitetexts:
        splits = text_splitter.split_text(page[target_key])
        page.pop(target_key, None)
        docs.extend(splits)
        metadatas.extend([page] * len(splits))

    return docs, metadatas


def split_df(df:pd.DataFrame, target:str) -> tuple[list[str], list[dict]]:
    texts = df[target].values

    meta_columns = df.columns.to_list()
    meta_columns.remove(target)

    meta_df = df[meta_columns]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0, separators=[" ", ".", ",", "\n"])

    documents, metadata = [], []

    for i, item in enumerate(texts):
        splits = text_splitter.split_text(item)
        splits = set(splits)
        documents.extend(splits)
        metadata.extend([meta_df.iloc[i].to_dict()] * len(splits))

    return documents, metadata



# -------------MODEL INTERACTIONS-----------------------
def get_model(model_name='gpt-3', temperature=0.7):
    return ChatOpenAI(model=MODELS[model_name], temperature=temperature)


# --------------RECCOMENDATION CHAINTS------------------
def news_from_query(query, country="IN", llm_name="gpt-3"):
    industry = query.split("|")[0]
    company_description = query.split("|")[1]
    news_topic_template = """What are the top 10 topic related to the {query} industry and a company with this description:
{description}
Only list the items as a set of comma seperated values, no numbering"""
    news_topic_prompt = PromptTemplate(template=news_topic_template, input_variables=['query', 'description'])
    news_topic_chain = LLMChain(llm=get_model(llm_name), prompt=news_topic_prompt, output_key="news_topics")

    news_topics = news_topic_chain({
        "query": industry,
        "description": company_description
    })["news_topics"]
    news_topics_query = re.sub(r",\s+", " OR ", news_topics)
    print("Returned news search: ", news_topics_query)

    return get_news_by_search(news_topics_query, country=country)


# -----------GENERATIVE RECCOMENDATION CHAINS AND FILTERING----------
def filter_news(query:str, chroma_reader:Reader, country_code:str="", query_extension:str=""):

    query = query# + "|" + query_extension

    _filter = None

    if not (country_code == "" or country_code == None):
        _filter={"country_code":country_code}

    relevant_docs = chroma_reader.search(query, filter=_filter)

    relevant_items = [{
            "title": document.page_content,
            "description": document.metadata['description'],
            'url': document.metadata['url'],
            'card_text': document.metadata['card_text'],
            'source': document.metadata['source'],
            "top_image": document.metadata['top_image'],
            'validation': {
                "google_trends": document.metadata["keywords"].split(",")
            }
        } for document in relevant_docs]

    return relevant_items


def run_simple_query(context, query, llm_name="gpt-3", temperature=0.7):
    template = """Given this context, answer this query: {query}

{context}
"""
    prompt = PromptTemplate(template= template, input_variables=['query', 'context'])
    chain = LLMChain(llm=get_model(llm_name, temperature=temperature), prompt=prompt, output_key='answer')

    return chain({
        "context": context,
        'query': query
        })['answer']


def generate_social_media_trends(
        content_category:str, 
        chroma_reader:Reader, 
        llm_name:str="gpt-3") -> list[dict]:

    llm = get_model(llm_name, temperature=1)

    query = f"{content_category} social media trends"

    relevant_docs = chroma_reader.search(query, n=15)
    relevant_docs_text = "\n".join([item.page_content.replace("\n", " ") for item in relevant_docs])

    template = """Given the following context, I want you to answer this query: {query}

CONTEXT:
{context}

INSTRUCTIONS:
I want you give me answer based on the context, only take information from the context, do not create your own ideas
I want you to give me creative answers and not just generic categories.
All answers should be different

Give me output in the following format only: 
<topic>||<2 word hashtag>||trending on <platform>
<topic>||<2 word hashtag>||trending on <platform>
and so on
"""

    prompt = PromptTemplate(template=template, input_variables=["query", "context"])
    chain = LLMChain(prompt=prompt, llm=llm, output_key="trends")

    output = chain({
        "query": f"Top 5 interesting social media trends about {content_category}",
        "context": relevant_docs_text
    })["trends"]

    output = re.sub("(\n)+", "\n", output)
    outputs = output.split("\n")
    outputs = [re.sub("^(\d+)\.?", "", output) for output in outputs]
    outputs = [re.sub("\s+\|\|\s+", "||", output) for output in outputs]

    sorted_headlines = [item for item in outputs if (len(item.split("||")) == 3)][:5]
    
    data = []

    for item in sorted_headlines:
        try:
            title, hashtag, reason = item.split("||")
        except:
            title, hashtag = item.split("||")[:2]
            reason = ""

        data.append({
            "title": title,
            "reason": reason,
            "validation": {
                "hashtag": get_hashtag_data(hashtag) # add best-hashtags function
            }
        })

    return data


def generate_current_events(company_description:str, chroma_reader:Reader, topic_list:list[str], keywords_dict:list[str], country_code:str, country:str, llm_name:str="gpt-3", temperature=0.2) -> list[dict]:
    query = f"List 5 important and interesting events related to any of these topics: {','.join(topic_list)}"

    print("getting holiday list")
    holidays = str(get_holidays(country_code=country_code)["name"].to_list())
    print(holidays)

    print("Search relevant documents")
    relevant_docs = []
    for topic in tqdm(topic_list):

        keywords = keywords_dict[topic]
        query = f"{topic} important events in {country} around the date {current_date()}"

        relevant_docs.extend(chroma_reader.search(
            query=query,
            n=5,
            filter={"country_code":country_code},
            keywords=keywords
        ))
    relevant_docs_text = "\n".join([item.page_content.replace("\n", " ") for item in relevant_docs])

#     template = """
# I am a marketing head and I am tasked to write social media content about big events around this date: {date}
# I am looking for important events to write some content (like Instagram post/reel, or Tiktok video, or Facebook post, or linkedin post, etc.).
# There is no specific topic that I am interested in, I write about general events/ideas.
# But I only write about events that have a massive reach within a country or worldwide (massive events in the specified is preferred).
# For example christmas which is celebrated all around the world, or diwali which is one of the biggest festivals in India, or grammy awards is the biggest music award show in the US, or FIFA world cup which is watched all over the world, etc.
# The above mentioned events are just examples that I would write content about.

# Important details:

# Country that I am writing about: {country}

# Date: {date}, This is the date around which I want to write content.

# Important calendar events for {country}: {holidays} (These have priority)

# I searched the internet about upcoming events, here is some data that you can use to suggest me what events I should write about:
# {context}

# VERY IMPORTANT:
# 1) DO NOT TELL ME ABOUT PRODUCTS OR SERVICES OF OTHER COMPANYS, NOR TELL ME THAT THERE ARE ANY SALES BECAUSE OF SOME FESTIVAL. 

# 2) ONLY LIST THOSE EVENTS THAT ARE GLOBALLY RELEVANT (EG. CHRISTMAS) OR RELEVANT TO {country} (LIKE CRICKET TO INDIA). 
# IF YOU TELL ME EVENTS THAT ARE NOT RELEVANT GLOBALLY OR TO {country} THEN I CANNOT WRITE ABOUT IT AND MY TIME, EFFORT AND MONEY WILL BE WASTED.

# 3) I HAVE GIVEN YOU A LIST OF CALANDAR EVENTS FOR {country}, THOSE HAVE A HIGHER PRIORITY.

# Give me output in the following format only: 
# <event name>||<topic>||<short reason>
# <event name>||<topic>||<short reason>
# and so on
# """

    template = """
I am a marketing head and I am tasked to write social media content about big events around this date: {date} or within the next month from this date.
I am looking for important events to write some content (like Instagram post/reel, or Tiktok video, or Facebook post, or linkedin post, etc.).
There is no specific topic that I am interested in, I write about general events/ideas.
But I only write about events that have a massive reach within a country or worldwide (massive events in the specified is preferred).
For example christmas which is celebrated all around the world, or diwali which is one of the biggest festivals in India, or grammy awards is the biggest music award show in the US, or FIFA world cup which is watched all over the world, etc.
The above mentioned events are just examples that I would write content about.    

Given the following context, I want you to answer this: {query}. 

Context:
{context}

Calendar events:
{holidays}

tell me about events relevant to {country}

Give me output in the following format only: 
<event name>||<topic>||<short reason>
<event name>||<topic>||<short reason>
and so on

Instructions:
* If there are important calendar events (like national day or a big religious festival) then always include those in your answer
* The order of events should represent how engaging the event might be.
* Do not restrict the events to only one or two categories like sports or film, there should be multiple categories if possible.
* List only those events that are currently going on, going to happen in 1 month, or have happened within 1 month of today's date.
* Only give me events that are positive.
* Events should be important on a global scale, example: sporting events, or international conferences like G20.
* Dont write numbering in the front
* Keep the items diverse, and prioritise events that have a large reach.
"""

    prompt = PromptTemplate(template=template, input_variables=["query", "date", "context", "country", "holidays"])
    chain = LLMChain(prompt=prompt, llm=get_model(llm_name, temperature=temperature), output_key="events")

    output = chain({ 
        "query": query,
        "date": current_date(),
        "context": relevant_docs_text,
        "holidays": ",".join(holidays),
        "country": country
    })["events"]

    # print(relevant_docs_text)
    print(output)

    output = re.sub("(\n)+", "\n", output)

    outputs = output.split("\n")
    outputs = [re.sub("^(\d+)\.?", "", k) for k in outputs]
    outputs = [re.sub("\s+\|\|\s+", "||", k) for k in outputs]

    sorted_headlines = [item for item in outputs if (len(item.split("||")) == 4) or (len(item.split("||")) == 3)]
    
    data = []

    for item in sorted_headlines:
        try:
            title, topic, reason = item.split("||")
        except:
            title, topic, sentiment = item.split("||")
            reason = ""

        data.append({
            "event_name": title,
            "validation": {
                "google_trends": [title]
            },
            "topic": topic
        })

    return data
