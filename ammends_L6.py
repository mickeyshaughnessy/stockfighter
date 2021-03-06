# this script collects evidence of insider trading 
# I followed the strategy outline here https://github.com/gavingmiller/level-6
#


from Stockfighter.Api import StockFighterApi

from sklearn.linear_model import LinearRegression as LR
import requests
import threading
from json import loads, dumps
from gevent import spawn, sleep
import numpy as np
import matplotlib.pyplot as plt
import random
import logging
from config import *
from pprint import pprint

headers = {"X-Starfighter-Authorization": key}
gm_url = 'https://www.stockfighter.io/gm'
log_level = logging.INFO
api = StockFighterApi(key, log_level)
account_data = {} 

# The strategy is for each account, to watch and see its executed orders
# Buys, sells, total volume
def received_message(m):
    try:
        if m.is_text:
            msg = loads(m.data.decode('utf-8'))
            threading.Thread(target=update_accounts, args=[msg]).start() 
    except ValueError:
        pass

def update_accounts(msg):
    acct = msg['account']
    order = msg['order']
    direction = order['direction']
    trans = []
    for f in order['fills']:
        trans.append((order['price'], order['qty']))
    if direction == 'sell':
        for t in trans:
            account_data[acct]['sells'].append(t)
            account_data[acct]['volume'] += t[1]
    else:
        for t in trans:
            account_data[acct]['buys'].append(t)
            account_data[acct]['volume'] += t[1]

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

def culprits(data):
    print len(data)
    # returns the most profitable accounts (by volume)
    # (name, profit, volume)
    # culprit should be highest profit and low volume
    accs, reg1, reg2 = {}, LR(fit_intercept=True), LR(fit_intercept=True)
    for acc in data:
        _buys, _sells = data[acc]['buys'], data[acc]['sells']
        profit = get_profit(_sells, _buys)
        volume = data[acc]['volume']
        # in sklearn, predictors are fit with ([<X>], [Y]), where <X> is a vector of features, and Y is a label
        #X1,X2 = [[x] for x in range(len(_buys))], [[x] for x in range(len(_sells))]
        #Y1, Y2 = [b[1] for b in _buys], [s[1] for s in _sells]
        #if X1 and X2 and Y1 and Y2:
        #    reg1.fit(X1,Y1), reg2.fit(X2, Y2)
        #    buy_intercept = reg1.intercept_ 
        #    sell_intercept = reg2.intercept_
        #else:
        #    buy_intercept, sell_intercept = 0,0
        if volume > 0:
            accs[acc] = {}
            #accs[acc]['profit'] = profit
            #accs[acc]['volume'] = volume 
            #accs[acc]['avg_sell'] = sell_intercept 
            #accs[acc]['avg_buy'] = buy_intercept
            accs[acc]['avg_profit'] = profit / (1.0*volume)
#            accs.append((acc, profit, data[acc]['volume'], sell_intercept, buy_intercept))
#    return sorted(accs, key=lambda acc : acc[1])[-10:]
    return accs 

def get_profit(buys, sells):
    bid, ask = quote() 
    if buys and sells:
        profit = 0
        for b in buys:
            profit -= b[0]*b[1]
        for s in sells:
            profit += s[0]*s[1]
        if bid and ask: 
            profit += 0.5 * (bid + ask) * (sum(b[0] for b in buys) - sum(s[0] for s in sells))
        return profit / 100.0            
    else: 
        return 0 

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
    for order in range(min(highest, 200)):
        acc = requests.delete('https://api.stockfighter.io/ob/api/venues/%s/stocks/%s/orders/%s' % (venue, stock, order), headers=headers).json()['error'].split(' ')[-1].replace('.','').rstrip()
        accounts.add(acc)
        if order % 10 == 0: print 'order %s' % order
    print 'There are %s unique accounts' % len(accounts)

    accounts = list(accounts)
    for acc in accounts:
        account_data[acc] = {'sells':[], 'buys':[], 'volume':0} 
    # set up websockets to listen to each account 
   
    socks = [api.stock_execution_socket(venue, stock, acc, received_message) for acc in accounts] 
    # websockets get closed if callback function takes too long

    print 'established execution websockets'

    while t < 100000:
        t += 1
        sleep(0.1)
        if t % 10 == 0:
            #suspects = [account_data[k] for k in account_data if account_data[k]['volume']>0]
            #pprint(suspects)
            print '###################'
            pprint(culprits(account_data))
        #if t % 1000:
        #    socks = [api.stock_execution_socket(venue, stock, acc, received_message) for acc in accounts] 
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
