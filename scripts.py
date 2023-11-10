from utils.simple_utils import *
from utils.google_utils import *
from utils.langchain_utils import *

from mongo.interface import *

import os
import time



def update_user_moments(user, mongo_client):
    _id = user["company_id"]
    company_name = user["company_name"]
    company_description = user["company_description"]
    country = user["country"]
    country_id = user["country_id"]


    # generate industry moments
    


if __name__ == "__main__":
    
    # Constants
    NEWS_TOPICS = read_lines_from_file("./config/topic-type.txt")
    QUERY_TOPICS = read_lines_from_file("./config/query-topics.txt")
    COUNTRY_NAMES = read_lines_from_file("./config/countries-names.txt")
    COUNTRY_CODES = defaultdict(None)
    for name, code in zip(COUNTRY_NAMES, read_lines_from_file("./config/countries-code.txt")):
        COUNTRY_CODES[name] = code


    # environment setup
    with open(".env", "r") as key_file:
        keys = list(key_file)

    for item in keys:
        variable, value = item.split("=")[0], "=".join(item.split("=")[1:])
        os.environ[variable] = value.replace("\n", "")

    user_mongo_client = MongoInterface(
        url=os.environ["MONGO_CONNECTION_STRING"],
        database="users",
        collection="user-data"
    )



