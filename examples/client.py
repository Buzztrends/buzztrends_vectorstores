import chromadb
from chromadb.utils import embedding_functions
from langchain.embeddings import OpenAIEmbeddings
import os


# FOR CLIENT CREATION USING HTTP CLIENT
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.environ["OPENAI_API_KEY"],
                model_name="text-embedding-ada-002"
            )

client  = chromadb.HttpClient() # host=> IP of host server and port=> port id of the server
collection = client.get_or_create_collection(name="test",embedding_function=openai_ef,metadata={"hnsw:space": "cosine"})