import pandas as pd
import os
import requests

from .simple_utils import current_date

def get_holidays_for_year(country_code:str, year:int, holiday_type:str="") -> pd.DataFrame:
    api_url = f'https://api.api-ninjas.com/v1/holidays?country={country_code}&year={year}&type={holiday_type}'

    print("Calling", api_url)

    response = requests.get(api_url, headers={'X-Api-Key': os.environ["API_NINJAS_KEY"]})

    if response.status_code == requests.codes.ok:
        data = response.json()

        df = pd.DataFrame.from_records(data, index=list(range(len(data))))
        df['date'] = pd.to_datetime(df["date"])
        df.sort_values("date", inplace=True)

        return df
    
    raise Exception(response.status_code, response.text)    

def get_holidays(country_code:str, holiday_type:str="", ignore_types:list[str]=["SEASON", "UNITED_NATIONS_OBSERVANCE", "STATE_OBSERVATION"]):
    now_date = current_date()
    year = int(now_date.split("-")[0])

    df1 = get_holidays_for_year(country_code, year, holiday_type=holiday_type)
    df2 = get_holidays_for_year(country_code, year+1, holiday_type=holiday_type)

    df = pd.concat((df1, df2)).reset_index(drop=True)
    df = df[~df["type"].isin(ignore_types)]
    df.set_index("date", inplace=True)

    now_date = pd.to_datetime(current_date())
    next_date = now_date + pd.Timedelta(days=30)
    df = df.loc[now_date:next_date]

    return df