import json
import requests
import sys
import os
from os import getenv
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
def decide_4me():
    
    BASE_YELP_URL = "https://api.yelp.com/v3/businesses/search"
    HEADERS = {'Authorization': 'Bearer %s' % getenv("FOOD_SELECTOR_API")}
    ########################
    # need input from Front end submit form for below
    user_local = 78666 #input("Enter zip-code or City")
    category = 'Thai'
    ########################
    PARAMS={'location' : user_local,
            'term' : category,
            'radius' : 6500,
            'open_now' : False,
            'limit' : 1, # depending on pure goal of app we want 1 or 3 #
    }

    yelp_response = requests.get(
        BASE_YELP_URL, params=PARAMS, headers=HEADERS
    )
    addr = yelp_response.json()['businesses'][0]['location']['display_address']
    img_url = yelp_response.json()['businesses'][0]['url']
    phone = yelp_response.json()['businesses'][0]['display_phone']
    rest_url = yelp_response.json()['businesses'][0]['url']
    
    eat_this_dict = {"Address": addr, "Image": img_url, "Phone": phone, "URL": rest_url}
    print(eat_this_dict)
    
decide_4me()


