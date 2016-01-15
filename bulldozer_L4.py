# this script deploys a market maker 
"""
curl https://api.stockfighter.io/ob/api/venues/AIOPEX/stocks/MEIA/quote --header "X-Starfighter-Authorization:d4f6f80befe9cd49a65f470a1acea0bb227a104b"
curl -X POST -d '{"orderType":"market","qty":1,"direction":"buy","account":"WLS28175343"}' https://api.stockfighter.io/ob/api/venues/MRBTEX/stocks/OGV/orders --header "X-Starfighter-Authorization:d4f6f80befe9cd49a65f470a1acea0bb227a104b"
"""

import requests
import json
from gevent import spawn, sleep
#from multiprocessing import Process
import numpy as np
import matplotlib.pyplot as plt

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

def depth():
    r = requests.get(url+'/quote', headers=headers)
    try:
        ask_depth, bid_depth = r.json().get('askDepth'), r.json().get('bidDepth')
    except:
        print r.text
    return bid_depth, ask_depth

def get_danger(level_ask=10000, level_bid=10000):
    bid_depth, ask_depth = depth()
    return bid_depth > level_bid, ask_depth > level_ask, bid_depth, ask_depth

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
    
    totalCash, netFilledOrders, orders, time = 0, 0, [], 0
    while 1:
        sleep(0.05)
        time += 1
        if time % 5 == 0:
            # pause and display NAV every 10 steps 
            plot_NAV()

        bid, ask =  quote()
        pos, _, _  = get_position()
        if bid and ask:
            sell_danger, buy_danger, bid_depth, ask_depth = get_danger(10000, 10000)
            #submit a pair of buy/sell orders
            if abs(pos) <= ls_limit and not buy_danger and not sell_danger:
                payload_selllimit = json.dumps({"orderType":"limit", "price":int(ask*1.05),"qty":default_qty,"direction":"sell","account":account})
                r1 = requests.post(url+'/orders', data=payload_selllimit, headers=headers)
                payload_buylimit = json.dumps({"orderType":"limit","price":int(bid*0.95),"qty":default_qty,"direction":"buy","account":account})
                r2 = requests.post(url+'/orders', data=payload_buylimit, headers=headers)
                orders.append(r1.json()['id'])
                orders.append(r2.json()['id'])
                print 'submitted buy/sell orders at %s - %s' % (bid*0.95, ask*1.05)
            elif pos < -ls_limit and not buy_danger and not sell_danger:
                # submit just a buy order (don't go too short)
                payload_buylimit = json.dumps({"orderType":"limit","price":int(bid*0.95),"qty":default_qty,"direction":"buy","account":account})
                r2 = requests.post(url+'/orders', data=payload_buylimit, headers=headers)
                orders.append(r2.json()['id'])
                print 'submitted buy order at %s' % (bid*0.95)
            elif pos > ls_limit and not buy_danger and not sell_danger:
                # submit just a sell order (don't go too long)
                payload_selllimit = json.dumps({"orderType":"limit", "price":int(ask*1.05),"qty":default_qty,"direction":"sell","account":account})
                r1 = requests.post(url+'/orders', data=payload_selllimit, headers=headers)
                orders.append(r1.json()['id'])
                print 'submitted sell order at %s' % (ask*1.05)
            elif buy_danger:
                totalCash, netFilledOrders = cancel_orders(orders, 'sell', totalCash, netFilledOrders)
                print 'sell danger detect, cancelling all sell orders. bid/ask depth is %s/%s' % (bid_depth, ask_depth)
                if pos < ls_limit:
                    payload_buylimit = json.dumps({"orderType":"limit","price":int(bid*0.95),"qty":default_qty,"direction":"buy","account":account})
                    r2 = requests.post(url+'/orders', data=payload_buylimit, headers=headers)
                    orders.append(r2.json()['id'])
                    print 'submitted buy order at %s' % (bid*0.95)

            elif sell_danger:
                totalCash, netFilledOrders = cancel_orders(orders, 'buy', totalCash, netFilledOrders)
                print 'buy danger detect, cancelling all buy orders. bid/ask depth is %s/%s' % (bid_depth, ask_depth) 
                if pos > -1*ls_limit:
                    payload_selllimit = json.dumps({"orderType":"limit", "price":int(ask*1.05),"qty":default_qty,"direction":"sell","account":account})
                    r1 = requests.post(url+'/orders', data=payload_selllimit, headers=headers)
                    orders.append(r1.json()['id'])
                    print 'submitted sell order at %s' % (ask*1.05)

            totalCash, netFilledOrders = remove_filled_orders(orders, totalCash, netFilledOrders)
            NAVs.append(totalCash + netFilledOrders*bid)

            while len(orders) > 5:
                # cancel stale outstanding orders, first from the exchange
                delete_order(orders[0])
                r = requests.get(url+'/orders/%s' % orders[0], headers=headers)
                # next, update the totalCash, netFilledOrders, and orders data.
                if r.json():
                    totalCash, netFilledOrders = update_vars(totalCash, netFilledOrders, r)
                # last, pop the order off our book.
                orders.pop(0)
            print ('bid: %s, ask: %s, position: %s total Cash ($): %s Stock Value($): %s Net Value ($): %s' % 
                (bid, ask, pos, totalCash/100.0, netFilledOrders*bid/100.0, (totalCash + netFilledOrders*bid)/100.0))
    
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

#def listen_websocket():
#    from websocket import create_connection
#    socket_str = 'wss://api.stockfighter.io/ob/api/ws/%s/venues/%s/executions' % (account, venue)
#    ws = create_connection(socket_str)
#    while 1:
#        sleep(0.5)
#        result =  ws.recv()
#        print type(result) 

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

def plot_NAV():
    plt.close()
    x = [i for i in range(len(NAVs))]
    plt.scatter(x, NAVs, s=50, alpha=0.5)
    plt.title('NAV over time')
    plt.xlabel('time')
    plt.ylabel('NAV')
    plt.show(block=False) 

if __name__ == '__main__':
    account, venue, stock = restart_level(key, 'dueling_bulldozers')
    base_url = 'https://api.stockfighter.io/ob/api/venues/%s/' % (venue)
    url = base_url + 'stocks/%s' % (stock)
    order_url = base_url + 'accounts/%s/orders' % (account)
    NAVs = []
    
    def Gspawn():
        G = [spawn(run_cautious, stock, venue)]
        [g.join() for g in G]
    
    Gspawn()            
    #P = [Process(target=Gspawn)]
    #[p.start() for p in P]
    #[p.join() for p in P]  
