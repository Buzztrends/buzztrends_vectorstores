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
    print("Updating user moments")
    # Create personalized industry news for every user
    userlist = user_mongo_client.get_user_list()[1:]

    with Pool(1) as pool:
        [item for item in pool.imap(update_user_moments, userlist)]