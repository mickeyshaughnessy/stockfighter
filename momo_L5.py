# this script deploys a market maker 
"""
curl https://api.stockfighter.io/ob/api/venues/AIOPEX/stocks/MEIA/quote --header "X-Starfighter-Authorization:d4f6f80befe9cd49a65f470a1acea0bb227a104b"
curl -X POST -d '{"orderType":"market","qty":1,"direction":"buy","account":"WLS28175343"}' https://api.stockfighter.io/ob/api/venues/MRBTEX/stocks/OGV/orders --header "X-Starfighter-Authorization:d4f6f80befe9cd49a65f470a1acea0bb227a104b"
"""

import requests
import json
from gevent import spawn, sleep
import numpy as np
import matplotlib.pyplot as plt

from config import *

headers = {"X-Starfighter-Authorization": key}
gm_url = 'https://www.stockfighter.io/gm'

def restart_level(key, level):
    r = requests.post(gm_url+'/levels/%s' % level, headers=headers)
    print r.text

    account, venue, ticker = r.json().get('account'), r.json().get('venues')[0], r.json().get('tickers')[0]
    return account, venue, ticker 

def quote():
    r = requests.get(url+'/quote', headers=headers)
    try:
        bid, ask = r.json().get('ask'), r.json().get('bid')
    except:
        print r.text
    return bid, ask

def depthAndSize():
    r = requests.get(url+'/quote', headers=headers)
    try:
        ask_depth, bid_depth, ask_size, bid_size = r.json().get('askDepth'), r.json().get('bidDepth'), r.json().get('askSize'), r.json().get('bidSize')
    except:
        print r.text
    return bid_depth, ask_depth, ask_size, bid_size

def get_danger(max_ask_ratio = 0.5, max_bid_ratio = 0.5):
    bid_depth, ask_depth, ask_size, bid_size = depthAndSize()

    bid_danger = False
    ask_danger = False
    if ((ask_size > 10000 and ask_depth > 200000) or (bid_size > 10000 and bid_depth > 200000)):
        ask_danger = True
    elif ((ask_size > 10000 and ask_depth < 100000 and ask_depth > bid_depth) or (bid_size > 10000 and bid_depth < 100000 and bid_depth > ask_depth)):
        bid_danger = True

    if bid_danger or ask_danger:
        print ('ask depth = %s ask size = %s bid depth = %s bid size = %s' % (ask_depth, ask_size, bid_depth, bid_size))

    return bid_danger, ask_danger

def run_basic():
    while 1:
        sleep(0.1)
        bid, ask =  quote()
        pos, buys, sells = get_position()
        
        if bid and ask:
            if abs(pos) <= ls_limit:
                payload_selllimit = json.dumps({"orderType":"immediate-or-cancel", "price":int(ask*1.01),"qty":50,"direction":"sell","account":account})
                r1 = requests.post(url+'/orders', data=payload_selllimit, headers=headers)
                payload_buylimit = json.dumps({"orderType":"immediate-or-cancel","price":int(bid*0.99),"qty":50,"direction":"buy","account":account})
                r2 = requests.post(url+'/orders', data=payload_buylimit, headers=headers)
            elif pos < -ls_limit:
                payload_buylimit = json.dumps({"orderType":"immediate-or-cancel","price":int(bid*0.99),"qty":50,"direction":"buy","account":account})
                r2 = requests.post(url+'/orders', data=payload_buylimit, headers=headers)
            elif pos > ls_limit:
                payload_selllimit = json.dumps({"orderType":"immediate-or-cancel", "price":int(ask*1.01),"qty":50,"direction":"sell","account":account})
                r1 = requests.post(url+'/orders', data=payload_selllimit, headers=headers)
            print ('bid: %s, ask: %s, position: %s' % (bid, ask, pos))  


def run_cautious(stock, venue):
    print 'account is %s, venue is %s.' % (account, stock)
    
    totalCash, netFilledOrders, orders, last5asks, last5bids, time, pos = 0, 0, [], [], [], 0, 0
#    meanBid, meanAsk = quote()
    count = 0;
    while 1:
        if len(orders) > 0:
            totalCash, netFilledOrders = remove_filled_orders(orders, totalCash, netFilledOrders)
        pos, _, _  = get_position()
        buy_danger, sell_danger = get_danger(0.5, 0.5)
        if sell_danger and not buy_danger:
            payload_buymarket = json.dumps({"orderType":"market","price":int(1.0),"qty":(ls_limit),"direction":"buy","account":account})
            r2 = requests.post(url+'/orders', data=payload_buymarket, headers=headers)
            orders.append(r2.json()['id'])
            while sell_danger:
                buy_danger, sell_danger = get_danger(0.5, 0.5)
                sleep(0.1)
        elif buy_danger and not sell_danger:
            payload_sellmarket = json.dumps({"orderType":"market","price":int(1.0),"qty":(ls_limit),"direction":"sell","account":account})
            r1 = requests.post(url+'/orders', data=payload_sellmarket, headers=headers)
            orders.append(r1.json()['id'])
            while buy_danger:
                buy_danger, sell_danger = get_danger(0.5, 0.5)
                sleep(0.1)
        if pos != 0 or (count % 50 == 0):
            if pos > 0:
                payload_sellmarket = json.dumps({"orderType":"market","price":int(1.0),"qty":(pos),"direction":"sell","account":account})
                r1 = requests.post(url+'/orders', data=payload_sellmarket, headers=headers)
                orders.append(r1.json()['id'])
            elif pos < 0:
                payload_buymarket = json.dumps({"orderType":"market","price":int(1.0),"qty":(-pos),"direction":"buy","account":account})
                r2 = requests.post(url+'/orders', data=payload_buymarket, headers=headers)
                orders.append(r2.json()['id'])
            
            totalCash, netFilledOrders = remove_filled_orders(orders, totalCash, netFilledOrders)
            pos, _, _  = get_position()
            print ('pos: %s total Cash ($): %s ' % (pos, totalCash/100.0))
            
        count = count + 1

def run_watcher(stock, venue):
    print 'account is %s, venue is %s.' % (account, stock)

    totalCash, netFilledOrders, orders, last5asks, last5bids, time, pos = 0, 0, [], [], [], 0, 0
    bids, asks = [], []
    count = 0;
    while 1:
        count += 1
        if count % 100 == 0: plot_bid_ask(bids, asks)
        bid, ask = quote()
        bids.append(bid)
        asks.append(ask)
 
def update_vars(totalCash, netFilledOrders, r):
    # This function updates the internal tracking variables after an order is resolved
    # r is a response from a delete_order request
    if r.json().get('fills'):
        for fill in list(r.json()['fills']):
            if r.json()['direction'] == 'buy':
                totalCash -= fill['price']*fill['qty']
                netFilledOrders += fill['qty']
            elif r.json()['direction'] == 'sell':
                totalCash += fill['price']*fill['qty']
                netFilledOrders -= fill['qty']
    return totalCash, netFilledOrders

def delete_order(order_id):
    r = requests.delete(url+'/orders/%s' % order_id, headers=headers)
    print 'canceled order %s ' % r.json()['id']

def cancel_orders(orders, direction, totalCash, netFilledOrders):
    # get the orders for the account
    # for every unfilled order in the cancel direction
    # cancel the order
    # remove the order from our orders book (maybe make this into a function, so partially filled orders get accounted for)
    for order in orders:
        # get the order
        r = requests.get(url+'/orders/%s' % order, headers=headers)
        # cancel the order if it matches
        if r.json().get("direction") == direction:
            delete_order(order) 
            totalCash, netFilledOrders = update_vars(totalCash, netFilledOrders, r)
            orders.remove(order)

    return totalCash, netFilledOrders
    
def remove_filled_orders(orders, totalCash, netFilledOrders):
    for order in orders:
        r = requests.get(url+'/orders/%s' % order, headers=headers)
        if r.json()['originalQty'] == r.json()['totalFilled']:
            delete_order(order)
            totalCash, netFilledOrders = update_vars(totalCash, netFilledOrders, r)
            orders.remove(order)
    return totalCash, netFilledOrders

def get_position():
    rOrders = requests.get(order_url, headers=headers)
    pos, buys, sells = 0, 0, 0
   
    for order in list(rOrders.json()['orders']):
        if order['direction'] == 'buy':
            buys += (order['originalQty'] - order['totalFilled'])
            pos += order['totalFilled']
        elif order['direction'] == 'sell':
            sells -= (order['originalQty'] - order['totalFilled'])
            pos -= order['totalFilled']

    return pos, buys, sells

def plot_bid_ask(bids, asks):
    plt.close()
    x = [i for i in range(len(bids))]
    plt.scatter(x, bids, s=50, alpha=0.5, label='bid')
    plt.scatter(x, asks, s=50, alpha=0.5, label='ask')
    #plt.plot([0,x[-1]], [25000000,25000000], color='r', linestyle='-', linewidth=2)
    plt.title('bid ask spread over time')
    plt.xlabel('time')
    plt.ylabel('bid / ask')
    plt.legend()
    plt.show(block=False) 
    

def plot_NAV():
    plt.close()
    x = [i for i in range(len(NAVs))]
    plt.scatter(x, NAVs, s=50, alpha=0.5)
    plt.plot([0,x[-1]], [25000000,25000000], color='r', linestyle='-', linewidth=2)
    plt.title('NAV over time')
    plt.xlabel('time')
    plt.ylabel('NAV')
    plt.show(block=False) 

if __name__ == '__main__':
    #account, venue, stock = restart_level(key, 'irrational_exurberance')
    account, venue, stock = restart_level(key, 'irrational_exuberance')
    base_url = 'https://api.stockfighter.io/ob/api/venues/%s/' % (venue)
    url = base_url + 'stocks/%s' % (stock)
    order_url = base_url + 'accounts/%s/orders' % (account)
    NAVs = []
    
    def Gspawn():
        #G = [spawn(run_cautious, stock, venue)]
        G = [spawn(run_watcher, stock, venue)]
        [g.join() for g in G]
    
    Gspawn()            
    #P = [Process(target=Gspawn)]
    #[p.start() for p in P]
    #[p.join() for p in P]  
