from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from chromadb import HttpClient
from langchain.vectorstores.chroma import Chroma
from langchain.embeddings import OpenAIEmbeddings
class Reader:
    def __init__(self,host:str, port:int,collection:str,openai_api_key:str) -> None:
        self.__embedding_function = OpenAIEmbeddingFunction(api_key=openai_api_key,model_name="text-embedding-ada-002")
        try:
            __client = HttpClient(host=host,port=port)
        except ValueError:
            raise Exception("Collection not found!!")
        else:
            self.retriever = Chroma(client=__client,collection_name=collection,embedding_function=OpenAIEmbeddings(openai_api_key=openai_api_key,model="text-embedding-ada-002"))

    def search(self,query):
        return self.retriever.search(query=query,search_type="similarity")
    
if __name__ == "__main__":
    r = Reader(host="localhost",port=8000,collection="my_test",openai_api_key="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")
    print(r.search("demo"))