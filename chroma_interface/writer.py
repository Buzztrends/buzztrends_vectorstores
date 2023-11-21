import chromadb
import requests
import uuid
import pandas as pd

from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from ..utils.simple_utils import divide_chunks

import os

def get_id(_str):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(_str)))

class Writer:
    def __init__(self,host:str,port:int,openai_api_key:str) -> None:
        self.host = host
        self.port = port
        self.openai_api_key = openai_api_key
        self.__client = chromadb.HttpClient(host=host,port=port)
        self.__embedding_function = OpenAIEmbeddingFunction(api_key=openai_api_key)
    def create_collection(self,collection_name:str,meta_data=None) -> None:
        """
        Create a new collection with the given name.

        Args:
            - collection__name: str, name of the collection that will be created
            - meta_data: (optional)
        
        Returns:
            - None

        Raises:
            - ValueError, if collection already exists
            - ValueError, if name is invalid
        """
        self.__client.create_collection(name=collection_name,embedding_function=self.__embedding_function,metadata=meta_data)

    def update(self,collection_name:str,documents:list[str],metadata=None,max_retries=3,ids=None,filter_duplicates=True) -> None:
        """
        Add the provided documents to the given collection.
        Args:
            - collection_name:str, the name of the collection in which the documents will be added
            - docs: the documents to be added in collection

        Returns:
            - None

        Raises:
            - ValueError, if collection doesn't exists.
        """


        count = 0

        if ids == None:
            ids = [get_id(str(d) + str(m)) for d, m in zip(documents, metadata)]

        if filter_duplicates:
            temp = pd.DataFrame({
                "ids": ids,
                "documents": documents,
                "metadata": metadata
            })

            temp.drop_duplicates("documents", inplace=True)
            ids = temp["ids"].to_list()
            documents = temp["documents"].to_list()
            metadata = temp["metadata"].to_list()
        
        print(f"Pushing {len(documents)} to chromadb")

        while count<max_retries:
            try:
                temp_collection = self.__client.get_collection(name=collection_name,embedding_function= self.__embedding_function)

                chunked_ids = divide_chunks(ids, 1000)
                chunked_documents = divide_chunks(documents, 1000)
                chunked_metadata = divide_chunks(metadata, 1000)

                for ids, documents, metadata in zip(chunked_ids, chunked_documents, chunked_metadata):
                    temp_collection.add(ids=ids,documents=documents,metadatas=metadata)
                return
            
            except requests.exceptions.ConnectTimeout:
                print("Chroma connection timed out, retrying")
                self.__client = chromadb.HttpClient(host=self.host,port=self.port)
                self.__embedding_function = OpenAIEmbeddingFunction(api_key=self.openai_api_key)
                count += 1

            except chromadb.errors.DuplicateIDError:
                print("Duplicate entry found")

    def delete_collection(self,collection_name:str) -> bool:
        """
        Deletes the collection with the provided collection name. It returns "True" if the deletion is successful else it returns "False".
        Args:
            - collection_name: str, name of the collection to delete
        Return:
            - True, if the deletion is successful
            - False, if the collection is not found 
        """
        try:
            self.__client.delete_collection(name=collection_name)
        except ValueError:
            return False
        else:
            return True
    
    def delete_entries(self, collection_name:str, where:dict=None, where_document:dict=None) -> bool:
        collection = self.__client.get_collection(collection_name)
        collection.delete(where=where, where_document=where_document)
    

if __name__ == "__main__":
    w = Writer(host="localhost",port=8000,openai_api_key=os.environ["OPENAI_API_KEY"])
    # w.create(collection_name="my_test")
    w.update("my_test",docs=["This is for demo"],meta_data=[{"title":"Demo"}])