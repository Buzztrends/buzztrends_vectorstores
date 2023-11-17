from .reader import Reader
from .writer import Writer

def get_reader_writer(host:str, port:str, openai_api_key:str, reader_collection_name:str=None)->tuple[Reader, Writer]:
    """
    Creates a chroma_interface.reader.Reader and chroma_interface.writer.Writer object according to given parameters

    Params:
    - host: (str) host address of chroma db
    - port: (int) port for chroma db
    - openai_api_key: (str) openai api key string for embeddings model
    - reader_collection_name (optional): (str) what collection name should the reader be initialized to

    Returns:
    tuple in Reader and Writer object
    """
    chroma_writer = Writer(
        host=host,
        port=port,
        openai_api_key=openai_api_key
    )

    chroma_reader = Reader(
        host=host,
        port=port,
        openai_api_key=openai_api_key
    )

    if reader_collection_name:
        chroma_reader.set_collection(collection_name=reader_collection_name)

    return chroma_reader, chroma_writer


def create_new_collection(reader:Reader, writer:Writer, collection_name:str)->None:
    """
    Creates a new collection for the given name, and deletes old one if it exists

    Params:
    - reader: (Reader) chroma_interface.reader.Reader object
    - writer: (Writer) chroma_interface.writer.Writer object
    - collection_name: (str) name of new collection to be created

    Returns:
    None
    """
    collections = [item.name for item in reader.list_collections()]
    print("Creating Collection:", collection_name)

    # remove old data if it exists in chroma
    if collection_name in collections:
        writer.delete_collection(collection_name)

    # create fresh collection
    writer.create_collection(collection_name)
    reader.set_collection(collection_name)