from chromadb import HttpClient
import os

from langchain.docstore.document import Document

from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

class Reader:
    
    def __init__(self,host:str, port:int, openai_api_key:str, collection:str=None) -> None:
        
        self.client = HttpClient(host=host,port=port)
        self.openai_api_key = openai_api_key
        self.embedding_function = OpenAIEmbeddingFunction(os.environ["OPENAI_API_KEY"])

        if collection:
            self.set_collection(collection)

    def search(self,query,n=20,filter:dict=None,keywords:list[str]=[],collection:str="") -> Document:
        
        where_documents = None

        if collection != "":
            self.set_collection(collection)

        if keywords != []:
            where_documents = {"$or":[{"$contains":item} for item in keywords]}

        results = self.collection.query(query_texts=[query], n_results=n, where=filter, where_document=where_documents)
        documents = results['documents'][0]
        metadata = results['metadatas'][0]

        data = [Document(page_content=d, metadata=m) for d, m in zip(documents, metadata)]

        return data

    def set_collection(self, collection_name:str) -> None:
        self.collection = self.client.get_or_create_collection(collection_name, embedding_function=self.embedding_function)

    def list_collections(self):
        return self.client.list_collections()

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