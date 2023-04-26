import json
import requests
import sys
import os
from os import getenv

API_KEY = os.getenv("FOOD_SELECTOR_API")

def decide_4me():
    BASE_YELP_URL = "https://api.yelp.com/v3/businesses/search"
    HEADERS = {'Authorization': 'bearer %s' % API_KEY}
    ###   might be diff - used to call
    # probs input from Front end submit form
    user_local = 78666 #input("Enter zip-code or City")
    
    PARAMS={'location' : user_local,
            'term' : 'Thai',
            'radius' : 6500,
            'open_now' : True,
            'limit' : 1, # depending on pure goal of app we want 1 or 3 #
    }

    yelp_response = requests.get(
        BASE_YELP_URL, params=PARAMS, headers=HEADERS
    )
    #addr = yelp_response.json["display_address"]
    #print(addr)
    #eat_this_dict = {""}

    formated = yelp_response.json()
    print(formated)
    

decide_4me()


# curl --request GET \
#      --url https://api.yelp.com/v3/events/awesome-event \
#      --header 'Authorization: Bearer API_KEY' \
#      --header 'accept: application/json'