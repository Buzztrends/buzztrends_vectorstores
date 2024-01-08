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

    user_idx = input("User ids ('a' for all): ")




    if user_idx == 'a':
        # Create personalized industry news for every user
        userlist = user_mongo_client.get_user_list()[:]
    else:
        user_idx = list(map(int, user_idx.split(',')))
        userlist = map(user_mongo_client.get_user, user_idx)
    print("Updating user moments")

    with Pool(int(os.environ["NUM_WORKERS"])) as pool:
        [item for item in pool.imap(update_user_moments, userlist)]