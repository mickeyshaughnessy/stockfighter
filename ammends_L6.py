# this script collects evidence of insider trading 
#

import requests
from json import loads, dumps
import json 
from gevent import spawn, sleep
import numpy as np
import matplotlib.pyplot as plt
from collections import deque

from config import *

headers = {"X-Starfighter-Authorization": key}
gm_url = 'https://www.stockfighter.io/gm'

def restart_level(key, level):
    r = requests.post(gm_url+'/levels/%s' % level, headers=headers)
    account, venue, ticker = r.json().get('account'), r.json().get('venues')[0], r.json().get('tickers')[0]
    return account, venue, ticker 

def quote():
    r = requests.get(url+'/quote', headers=headers)
    try:
        bid, ask = r.json().get('ask'), r.json().get('bid')
    except:
        print r.text
    return bid, ask

def make_order():
    payload = json.dumps({"orderType":"market","qty":1,"direction":"buy","account": account})
    r = requests.post(
        "https://api.stockfighter.io/ob/api/venues/%s/stocks/%s/orders/" %
        (venue, stock),
        data=payload, headers=headers)
    return r.json().get('id')

def get_all_orders(last_id):
    return 0

def run_watcher():
    print 'account is %s, venue is %s, stock is %s.' % (account, venue, stock)
    id1, id2, t, orders = make_order(), make_order, 0, {}
    print last_id
    while 1:
        t += 1
        if t % 100 == 0:
            #orders = get_all_orders(last_id)
            print make_order() 

if __name__ == '__main__':
    account, venue, stock = restart_level(key, 'making_amends')
    base_url = 'https://api.stockfighter.io/ob/api/venues/%s/' % (venue)
    'https://api.stockfighter.io/ob/api/venues/TESTEX/accounts/EXB123456/stocks/FOOBAR/orders'    

    url = base_url + 'stocks/%s' % (stock)
    order_url = base_url + 'accounts/%s/orders' % (account)

    G = [spawn(run_watcher, )]
    [g.join() for g in G]
