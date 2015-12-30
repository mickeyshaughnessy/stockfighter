# this script makes an order
"""
curl -X POST -d '{"orderType":"market","qty":1,"direction":"buy","account":"EMS12164524"}' https://api.stockfighter.io/ob/api/venues/RKIMEX/stocks/BMOY/orders --header "X-Starfighter-Authorization:d4f6f80befe9cd49a65f470a1acea0bb227a104b"
"""
import requests
import json

from config import *

headers = {"X-Starfighter-Authorization": key}
payload = json.dumps({"orderType":"market","qty":50,"direction":"buy","account": account})

ordered = 0
while ordered < 101000:
    r = requests.post(
        "https://api.stockfighter.io/ob/api/venues/%s/stocks/%s/orders/" % 
        (venue, stock), 
        data=payload, headers=headers)
    print r 
    #ordered += int(r.json()['totalFilled'])
    ordered += int(r.json().get('totalFilled'))
    if ordered % 1000 == 0:
        print ordered
        print r.text
