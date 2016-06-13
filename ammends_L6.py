# this script collects evidence of insider trading 
#

from Stockfighter.Api import StockFighterApi

import requests
from json import loads, dumps
from gevent import spawn, sleep
import numpy as np
import matplotlib.pyplot as plt
import random
import logging
from config import *

headers = {"X-Starfighter-Authorization": key}
gm_url = 'https://www.stockfighter.io/gm'
log_level = logging.DEBUG
api = StockFighterApi(key, log_level)

def received_message(m):
    try:
        if m.is_text:
            msg = loads(m.data.decode('utf-8'))
            print msg
    except ValueError:
        pass

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
    direc = random.choice(['buy', 'sell'])
    payload = dumps({"orderType":"market","qty":1,"direction":direc,"account": account})
    r = requests.post(
        "https://api.stockfighter.io/ob/api/venues/%s/stocks/%s/orders/" %
        (venue, stock),
        data=payload, headers=headers)
    return r.json().get('id')

def get_all_orders(last_id):
    return 0

def get_order(o):
    order_url = url + '/orders/%s' % o
    r = requests.get(order_url, headers=headers)
    return r.json() 

def fill_orders(orders, last_id):
    new_id = make_order() 
    for o_id in range(last_id, new_id):
        orders[o_id] = get_order(o_id)
        print orders[o_id]
    return new_id  

    #ins = set([o for o in orders.keys() if o > _id])
    #new_id = make_order() 
    #alls = set(xrange(_id, new_id))
    #missing = ins ^ alls
    #for o in missing:
    #    orders[o] = get_order(o)
    #return new_id

def run_watcher():
    print 'account is %s, venue is %s, stock is %s.' % (account, venue, stock)
    _id, t, orders, accounts = 0, 0, {}, set([])
    
    # get highest order number
    resp = requests.get('https://api.stockfighter.io/ob/api/venues/%s/stocks/%s/orders/99999999' % (venue, stock), headers=headers).json()
    highest = int(resp['error'].split(' ')[-1].replace(')',''))
    print 'highest order is %s' % highest
   
    # get all the accounts  
    print 'getting all accounts...'
    accounts = set([])
    #for order in range(max(highest, 2000)):
    for order in range(100):
        acc = requests.delete('https://api.stockfighter.io/ob/api/venues/%s/stocks/%s/orders/%s' % (venue, stock, order), headers=headers).json()['error'].split(' ')[-1].replace('.','').rstrip()
        accounts.add(acc)
        if order % 10 == 0: print 'order %s' % order
    print 'There are %s unique accounts' % len(accounts)

    accounts = list(accounts)
    # set up websockets to listen to each account 
   
    socks = [api.stock_execution_socket(venue, stock, acc, received_message) for acc in accounts] 

    while 1:
        sleep(0.1)
    #    # watch the market
    #    # every once in a while, refresh the orders dict
    #    t += 1
    #    if t % 100 == 0:
    #        _id = fill_orders(orders, _id) 
    #        accounts.update([orders[o]['account'] for o in orders.keys()])
    #        print accounts 
                 
    
if __name__ == '__main__':
    account, venue, stock = restart_level(key, 'making_amends')
    base_url = 'https://api.stockfighter.io/ob/api/venues/%s/' % (venue)
    'https://api.stockfighter.io/ob/api/venues/TESTEX/accounts/EXB123456/stocks/FOOBAR/orders'    

    url = base_url + 'stocks/%s' % (stock)

    G = [spawn(run_watcher, )]
    [g.join() for g in G]
