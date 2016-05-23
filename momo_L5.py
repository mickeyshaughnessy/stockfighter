# this script deploys a bid/ask spread watcher
#
# The basic strategy is to buy low - sell high. You can do this in any order.
# The bots will increase the price as long as other bots are buying.

# To take advantage of it:
# 1. ignite buying by selling a few at low price.
# 2. Once the run starts, buy all available stock for a certain time period
# 3. Then, set a big sell at ~ 2x the intial price.
# 4. Then set several small sells (~4x) to unwind position.
# 5. repeat. 
 

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



def get_our_orders(venue, account, stock):
    base_url = 'https://api.stockfighter.io/ob/api/'   
    order_url = base_url+'/venues/%s/accounts/%s/stocks/%s/orders'% (venue, account, stock)
    r = requests.get(order_url, headers=headers)
    orders = loads(r.text)

    position = {True:0, False:0} 
    volume = {True:0, False:0} 

    for order in orders['orders']:
        buy = order['direction'] == 'buy'
        for fill in order['fills']:
            position[buy] += fill['qty'] * fill['price'] 
            volume[buy] += fill['qty']
            #print buy, fill, cash, stock_value

    NAV = position[False] - position[True] 
    print NAV/100.0, volume[True] - volume[False]

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
        get_our_orders(venue, account, stock)
        count += 1
        #if count % 10 == 0: plot_bid_ask(bids, asks)
        
        bid, ask = quote()
        if not bid: bid = -1
        if not ask: ask = -1

        bids.append(bid)
        asks.append(ask)

def plot_bid_ask(bids, asks):
    plt.close()
    x = range(len(bids)) 
    plt.scatter(x, bids, s=50, alpha=0.5, label='bid', marker='x', color='r')
    plt.scatter(x, asks, s=50, alpha=0.5, label='ask', marker='o', color='g')
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
