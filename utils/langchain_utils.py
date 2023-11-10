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


MODELS = json.load(open("./config/openai-models.json", 'r'))


# ------------DOCUMENT INTERACTIONS---------------------
def load_df(df, page_content_column="title"):
    return DataFrameLoader(df, page_content_column=page_content_column).load()


# -------------MODEL INTERACTIONS-----------------------
def get_model(model_name='gpt-3'):
    return ChatOpenAI(model=MODELS[model_name])

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

