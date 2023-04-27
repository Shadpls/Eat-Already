import json
import requests
import os
from os import getenv
from dotenv import load_dotenv, find_dotenv
import random

load_dotenv(find_dotenv())


def decide_4me():
    BASE_YELP_URL = "https://api.yelp.com/v3/businesses/search"
    HEADERS = {"Authorization": "Bearer %s" % getenv("FOOD_SELECTOR_API")}
    ########################
    # need input from Front end submit form for below
    user_local = "austin"  # input("Enter zip-code or City")
    category = ""
    ########################
    PARAMS = {
        "location": user_local,
        "term": category,
        "radius": 6500,
        "open_now": True,
        "limit": 1,  # depending on pure goal of app we want 1 or 3 #
    }

    yelp_response = requests.get(BASE_YELP_URL, params=PARAMS, headers=HEADERS)

    data = yelp_response.json()

    restaurant = random.choice(data["businesses"])

    print(data)

    # print(restaurant["name"])
    # print(restaurant["location"]["address1"])

    addr = restaurant["location"]["display_address"]
    name = restaurant["name"]
    img_url = restaurant["url"]
    phone = restaurant["display_phone"]
    rest_url = restaurant["url"]

    eat_this_dict = {
        "Name": name,
        "Address": addr,
        "Image": img_url,
        "Phone": phone,
        "URL": rest_url,
    }
    # print(eat_this_dict)


decide_4me()
