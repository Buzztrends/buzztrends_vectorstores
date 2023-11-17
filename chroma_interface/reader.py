from chromadb import HttpClient
from langchain.vectorstores.chroma import Chroma
from langchain.embeddings import OpenAIEmbeddings
import os

class Reader:
    
    def __init__(self,host:str, port:int, openai_api_key:str, collection:str=None) -> None:

        try:
            self.__client = HttpClient(host=host,port=port)
            self.openai_api_key = openai_api_key
        except ValueError:
            raise Exception("Collection not found!!")
        
        if collection:
            self.set_collection(collection)

    def search(self,query,n=20,filter=None):
        return self.collection.similarity_search(query=query, search_type="similarity", k=n, filter=filter)
    
    def set_collection(self, collection_name:str) -> None:
        self.collection = Chroma(
            client=self.__client,
            collection_name=collection_name,
            embedding_function=OpenAIEmbeddings(
                openai_api_key=self.openai_api_key,
                model="text-embedding-ada-002"
            )
        )

    def list_collections(self):
        return self.__client.list_collections()

    def filter_news(self, query:str, query_extension:str="", collection_name:str=None):
        query = query + "|" + query_extension

        if collection_name:
            self.set_collection(collection_name)

        relevant_docs = self.search(query)

        return [{
                "title": document.page_content,
                "description": document.metadata["description"],
                "url": document.metadata["link"],
                "card_text": document.metadata["card_text"],
                "source": document.metadata["source_name"],
                "top_image": document.metadata["image_url"],
                "validation": {
                    "google_trends": [document.metadata["keywords"].split(',')]
                }
            } for document in relevant_docs]

    
if __name__ == "__main__":
    r = Reader(host="localhost",port=8000,collection="my_test",openai_api_key=os.environ["OPENAI_API_KEY"])
    print(r.search("demo"))