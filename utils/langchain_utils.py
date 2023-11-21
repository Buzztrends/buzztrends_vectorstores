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


# -----------GENERATIVE RECCOMENDATION CHAINS----------
def filter_news(query:str, chroma_reader:Reader, query_extension:str=""):

    query = query + "|" + query_extension

    relevant_docs = chroma_reader.search(query)

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
                "hashtag": best_hashtag_get_popular(hashtag) # add best-hashtags function
            }
        })

    return data


def generate_current_events(chroma_reader:Reader, topic_list:list[str], country_code:str, llm_name:str="gpt-3") -> list[dict]:

    query = f"List 10 important and interesting events related to any of these topics: {','.join(topic_list)}."

    relevant_docs = chroma_reader.search(query, 30, {"country_": country_code})
    relevant_docs_text = "\n".join([item.page_content.replace("\n", " ") for item in relevant_docs])

    template = """Given the following context, I want you to answer this: {query}. Today's date {date}

Context:
{context}

Give me output in the following format only: 
<event name>||<topic>||<short reason>
<event name>||<topic>||<short reason>
and so on

Instructions:
1. The order of events should represent how engaging the event might be.
2. Do not restrict the events to only one or two categories like sports or film, there should be multiple categories if possible.
3. List only those events that are currently going on, going to happen in 1 month, or have happened within 1 month of today's date.
4. Only give me events that having a positive sentiment.
5. Events should be important on a global or a national scale, example: sporting events like cricket tournament, international conferences like G20 or BRICS, religious festival like christmas or eid, etc.
6. Dont write numbering in the front
7. Keep the items diverse, and prioritise events that have a large reach.
8. Do not repeat ideas. 
"""

    prompt = PromptTemplate(template=template, input_variables=["query", "context", "date"])
    chain = LLMChain(prompt=prompt, llm=get_model(llm_name, temperature=0.2), output_key="events")

    output = chain({ 
        "query": query,
        "date": current_date(),
        "context": relevant_docs_text
    })["events"]

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