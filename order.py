# this script makes an order
"""
curl -X POST -d '{"orderType":"market","qty":1,"direction":"buy","account":"EMS12164524"}' https://api.stockfighter.io/ob/api/venues/RKIMEX/stocks/BMOY/orders --header "X-Starfighter-Authorization:d4f6f80befe9cd49a65f470a1acea0bb227a104b"
"""


import requests
import json

headers = {"X-Starfighter-Authorization": "d4f6f80befe9cd49a65f470a1acea0bb227a104b"}
payload = json.dumps({"orderType":"market","qty":100,"direction":"buy","account":"EMS12164524"})
print type(payload)


ordered = 0
while ordered < 100000:
    r = requests.post("https://api.stockfighter.io/ob/api/venues/RKIMEX/stocks/BMOY/orders/", data=payload, headers=headers)
    ordered += int(r.json()['totalFilled'])
    if ordered % 1000 = 0:
        print ordered
        print r.text
