import requests
import bs4


def process_data(data):
    if data[0] == []:
        data = data[1:]

    for i in range(len(data)):
        data[i][2] = int(data[i][2].replace(",", ""))

    return_dict = {}
    for i in range(len(data)):
        return_dict[data[i][1]] = return_dict[i][2]
    return return_dict

def best_hashtag_get_popular(query:str):
    """
    Scrape popular hashtags from best hashtags

    Args:
        query:str, query to search hash tags
    
    Return:
        dict[list]= keys = [table,hashtags]

    """
    print("[GET] Popular hashtags")
    query= query.lower()
    query = query.replace(" ", "")
    try:
        url = f"http://best-hashtags.com/hashtag/{query}"
    except Exception as e:
        print("[FAILED] Popular hashtags")
        return {"hashtags":[],"table":[]}
    
    resp = requests.get(url)
    soup = bs4.BeautifulSoup(resp.text,"lxml")
    popualr = soup.find("div",dict(id="popular"))
    if popualr is None:
        print("No data in popular")
        raise Exception()


    data = []
    rows = popualr.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele])
    
    return process_data(data)


def best_hashtag_get_easy(query:str):
    """

    Scrape easy hashtags from best hashtags

    Args:
        query:str, query to search hash tags
    
    Return:
        dict[list]= keys = [table,hashtags]

    """
    query= query.lower()
    query = query.replace(" ", "")
    print("[GET] Easy hashtags for", query)

    try:
        url = f"http://best-hashtags.com/hashtag/{query}"
    except Exception as e:
        print("[FAILED] Easy hashtags")
        return {"hashtags":[],"table":[]}
    resp = requests.get(url)
    soup = bs4.BeautifulSoup(resp.text,"lxml")
    popualr = soup.find("div",dict(id="easy"))
    if popualr is None:
        print("No data in easy")
        raise Exception()


    data = []
    rows = popualr.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele])

    return process_data(data)


def best_hashtag_get_medium(query:str):
    """

    Scrape medium hashtags from best hashtags

    Args:
        query:str, query to search hash tags
    
    Return:
        dict[list]= keys = [table,hashtags]

    """
    print("[GET] Medium hashtags")
    query= query.lower()
    query = query.replace(" ", "")
    try:
        url = f"http://best-hashtags.com/hashtag/{query}"
    except Exception as e:
        print("[FAILED] Medium hashtags")
        return {"hashtags":[],"table":[]}
    
    resp = requests.get(url)
    soup = bs4.BeautifulSoup(resp.text,"lxml")
    popualr = soup.find("div",dict(id="medium"))
    if popualr is None:
        print("No data in medium")
        raise Exception()


    data = []
    rows = popualr.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele])
    
    return process_data(data)


def best_hashtag_get_related(query:str):
    """

    Scrape related hashtags from best hashtags

    Args:
        query:str, query to search hash tags
    
    Return:
        dict[list]= keys = [table,hashtags]

    """
    print("[GET] Related hashtags")
    query= query.lower()
    query = query.replace(" ", "")
    try:
        url = f"http://best-hashtags.com/hashtag/{query}"
    except Exception as e:
        print("[FAILED] Related hashtags")
        return {"hashtags":[],"table":[]}
    resp = requests.get(url)
    soup = bs4.BeautifulSoup(resp.text,"lxml")
    popualr = soup.find("div",dict(id="related"))
    if popualr is None:
        print("no data in related")
        raise Exception()

    data = []
    rows = popualr.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele])
    return process_data(data)

def parse_query(query:str):
    query = query.lower()
    query = query.replace(" ", "")

    print("parsed hashtag query:", query)
    return query

def get_hashtag_data(query:str):
    call_order = [best_hashtag_get_related, best_hashtag_get_easy, best_hashtag_get_medium, best_hashtag_get_popular]
    
    query = parse_query(query)

    for i in range(len(call_order)):
        try:
            return call_order[i](query)
        except Exception as e:
            i += 1

    return {
        "None": 0
    }

    