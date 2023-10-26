import chromadb
import uuid
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
class Writer:
    def __init__(self,host:str,port:int,openai_api_key:str) -> None:
        self.__client = chromadb.HttpClient(host=host,port=port)
        self.__embedding_function = OpenAIEmbeddingFunction(api_key=openai_api_key)
    def create(self,collection_name:str,meta_data=None) -> None:
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

    def update(self,collection_name:str,docs:list[str],meta_data=None) -> None:
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

        temp_collection = self.__client.get_collection(name=collection_name,embedding_function= self.__embedding_function)
        temp_collection.add(ids=[str(uuid.uuid1()) for _ in range(len(docs))],documents=docs,metadatas=meta_data)

    def delete(self,collection_name:str) -> bool:
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