from langchain.vectorstores.chroma import Chroma
import chromadb
from chromadb.utils import embedding_functions
"""
How to use client vector store in langchain?
Step 1: create a client using "chromadb" client. Here we are using HttpClient for client-server Architecture.

Step 2: Use the client in "langchain.vectorstores" for retrieval
"""
embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key="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",
                model_name="text-embedding-ada-002"
            )

# Step - 1:
persistent_client = chromadb.HttpClient()
collection = persistent_client.get_or_create_collection("collection_name")
collection.add(ids=["1", "2", "3"], documents=["a", "b", "c"])

# Step - 2:
langchain_chroma = Chroma(
    client=persistent_client,
    collection_name="collection_name",
    embedding_function=embedding_function,
)