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

def run_watcher(stock, venue):
    print 'account is %s, venue is %s.' % (account, stock)

    totalCash, netFilledOrders, orders, last5asks, last5bids, time, pos = 0, 0, [], [], [], 0, 0
    bids, asks = deque(maxlen=10000), deque(maxlen=10000) 
    count = 0;
    while 1:
        count += 1
        if count % 10 == 0: plot_bid_ask(bids, asks)
        
        bid, ask = quote()
        if not bid: bid = -1
        if not ask: ask = -1

        bids.append(bid)
        asks.append(ask)

def plot_bid_ask(bids, asks):
    plt.close()
    x = range(len(bids)) 
    plt.scatter(x, bids, s=50, alpha=0.5, label='bid', marker='x')
    plt.scatter(x, asks, s=50, alpha=0.5, label='ask', marker='o')
    plt.title('bid ask spread over time')
    plt.xlabel('time')
    plt.ylabel('bid / ask')
    plt.legend()
    plt.draw() 
    plt.pause(3)

if __name__ == '__main__':
    account, venue, stock = restart_level(key, 'irrational_exuberance')
    base_url = 'https://api.stockfighter.io/ob/api/venues/%s/' % (venue)
    url = base_url + 'stocks/%s' % (stock)
    order_url = base_url + 'accounts/%s/orders' % (account)
    NAVs = []

    #def Gspawn():
    G = [spawn(run_watcher, stock, venue)]
    [g.join() for g in G]
    
    #Gspawn()            
