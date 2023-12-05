from pymongo.mongo_client import MongoClient
import random
import os

class MongoInterface:
    def __init__(self, url, database, collection) -> None:
        self.client = MongoClient(url)[database][collection]

    def get_user_list(self):
        """
        Returns a cursor for all users

        Parameters:
        None 
        
        Returns:
        pymongo.cursor.Cursor
        """
        return self.client.find()

    def add_user(self, company_name, username, password, company_description, content_category, country, country_code):
        """
        Adds a new user to the system.

        Parameters:
        company_name (str): The name of the company.
        username (str): The username of the user.
        password (str): The password of the user.
        company_description (str): A description of the company.
        content_category (str): The category of content the company is interested in.

        Returns:
        None
        """
        company_id = random.randint(100000, 999999)
        moments = {
            "vectorstore_collection_id": company_id,
            "general_news": [],
            "industry_news": [],
            "current_events": [],
            "social_media": []
        }
        saved_items = [],
        last_5_generations = []

        return self.client.insert_one({
            "company_id": company_id,
            "company_name": company_name,
            "username": username,
            "password": password,
            "company_description": company_description,
            "content_category": content_category,
            "country": country,
            "country_code": country_code,
            "moments": moments,
            "saved_items": saved_items,
            "last_5_generations": last_5_generations
        })
    
    def get_user(self, _id):
        return self.client.find_one({"company_id":_id})

    def update_user_moments(self, _id, moments):
        """
        Update the moments for a user

        Parameters:
        _id (int): Company's id which has to be updated
        moments: new moments for the company

        Returns:
        None
        """
        new_values = {"$set": {"moments": moments}}
        return self.client.update_one({"company_id":_id}, new_values)
        