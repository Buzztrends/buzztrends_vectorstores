from utils.simple_utils import *
from utils.google_utils import *
from utils.langchain_utils import *

from mongo.interface import *

from chroma_interface import *
from chroma_interface.reader import Reader
from chroma_interface.writer import Writer

from script import *

import os
import time
# Constants
# NEWS_TOPICS = read_lines_from_file("./config/topic-type.txt")
# QUERY_TOPICS = read_lines_from_file("./config/query-topics.txt")
# COUNTRY_NAMES = read_lines_from_file("./config/countries-names.txt")
# COUNTRY_CODES = defaultdict(None)
# for name, code in zip(COUNTRY_NAMES, read_lines_from_file("./config/countries-code.txt")):
#     COUNTRY_CODES[name] = code

61176207,32575585
# environment setup
with open(".env", "r") as key_file:
    keys = list(key_file)

for item in keys:
    variable, value = item.split("=")[0], "=".join(item.split("=")[1:])
    os.environ[variable] = value.replace("\n", "")

chroma_reader, chroma_writer = get_reader_writer(
    host=os.environ["CHROMA_IP"],
    port=int(os.environ["CHROMA_PORT"]),
    openai_api_key=os.environ["OPENAI_API_KEY"]
)

user_mongo_client = MongoInterface(
    url=os.environ["MONGO_CONNECTION_STRING"],
    database="users",
    collection="user-data"
)


if __name__ == "__main__":
    # connect to MongoDB endpoint
    user_mongo_client = MongoInterface(
        url=os.environ["MONGO_CONNECTION_STRING"],
        database="users",
        collection="user-data"
    )

    which_ones = int(input("1 for general news, 2 for current events, 3 for both"))

    if which_ones == 1:
        get_general_news_data()

    if which_ones == 2:
        get_current_events()

    if which_ones == 3:
        # Common data, General news and current affairs
        # 1: General Dataset extraction
        # Start a branching process for general news extraction
        print("Starting general news extraction process")
        general_news_process = Process(target=get_general_news_data, args=())
        general_news_process.start()

        # 2: Current events
        print("Starting current events extraction process")
        get_current_events()
        
        # Wait for both processes to finish before proceeding
        general_news_process.join()