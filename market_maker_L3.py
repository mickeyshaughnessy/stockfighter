# this script deploys a market maker 
"""
curl https://api.stockfighter.io/ob/api/venues/AIOPEX/stocks/MEIA/quote --header "X-Starfighter-Authorization:d4f6f80befe9cd49a65f470a1acea0bb227a104b"
curl -X POST -d '{"orderType":"market","qty":1,"direction":"buy","account":"WLS28175343"}' https://api.stockfighter.io/ob/api/venues/MRBTEX/stocks/OGV/orders --header "X-Starfighter-Authorization:d4f6f80befe9cd49a65f470a1acea0bb227a104b"
"""

import requests
import json
from gevent import spawn, sleep
from multiprocessing import Process

from config import *

base_url = 'https://api.stockfighter.io/ob/api/venues/%s/' % (venue)
url = base_url + 'stocks/%s' % (stock)
order_url = base_url + 'accounts/%s/orders' % (account)
headers = {"X-Starfighter-Authorization": key}
payload_buymarket = json.dumps({"orderType":"market","qty":1,"direction":"buy","account":account})

def quote():
    r = requests.get(url+'/quote', headers=headers)
    try:
        bid, ask = r.json().get('ask'), r.json().get('bid')
    except:
        print r.text
    return bid, ask
 
def run_basic():
    while 1:
        sleep(0.1)
        bid, ask =  quote()
        pos, buys, sells = get_position()
        
        if bid and ask:
            if abs(pos) <= 450:
                payload_selllimit = json.dumps({"orderType":"immediate-or-cancel", "price":int(ask*1.01),"qty":50,"direction":"sell","account":account})
                r1 = requests.post(url+'/orders', data=payload_selllimit, headers=headers)
                payload_buylimit = json.dumps({"orderType":"immediate-or-cancel","price":int(bid*0.99),"qty":50,"direction":"buy","account":account})
                r2 = requests.post(url+'/orders', data=payload_buylimit, headers=headers)
            elif pos < -450:
                payload_buylimit = json.dumps({"orderType":"immediate-or-cancel","price":int(bid*0.99),"qty":50,"direction":"buy","account":account})
                r2 = requests.post(url+'/orders', data=payload_buylimit, headers=headers)
            elif pos > 450:
                payload_selllimit = json.dumps({"orderType":"immediate-or-cancel", "price":int(ask*1.01),"qty":50,"direction":"sell","account":account})
                r1 = requests.post(url+'/orders', data=payload_selllimit, headers=headers)
            print ('bid: %s, ask: %s, position: %s' % (bid, ask, pos))  

def run_limit():
    totalCash = 0;
    netFilledOrders = 0;
    orders = []
    while 1:
        sleep(0.1)
        bid, ask =  quote()
        pos, _, _  = get_position()
        if bid and ask:
            if abs(pos) <= 450:
                payload_selllimit = json.dumps({"orderType":"limit", "price":int(ask*1.05),"qty":50,"direction":"sell","account":account})
                r1 = requests.post(url+'/orders', data=payload_selllimit, headers=headers)
                payload_buylimit = json.dumps({"orderType":"limit","price":int(bid*0.95),"qty":50,"direction":"buy","account":account})
                r2 = requests.post(url+'/orders', data=payload_buylimit, headers=headers)
                orders.append(r1.json()['id'])
                orders.append(r2.json()['id'])
                print 'submitted buy/sell orders at %s - %s' % (bid*0.95, ask*1.05)
            elif pos < -450:
                payload_buylimit = json.dumps({"orderType":"limit","price":int(bid*0.95),"qty":50,"direction":"buy","account":account})
                r2 = requests.post(url+'/orders', data=payload_buylimit, headers=headers)
                orders.append(r2.json()['id'])
                print 'submitted buy order at %s' % (bid*0.95)
            elif pos > 450:
                payload_selllimit = json.dumps({"orderType":"limit", "price":int(ask*1.05),"qty":50,"direction":"sell","account":account})
                r1 = requests.post(url+'/orders', data=payload_selllimit, headers=headers)
                orders.append(r1.json()['id'])
                print 'submitted sell order at %s' % (ask*1.05)

            totalCash, netFilledOrders = remove_filled_orders(orders, totalCash, netFilledOrders)

            while len(orders) > 20:
                order_id = orders[0]
                delete_order(order_id)
                r = requests.get(url+'/orders/%s' % order_id, headers=headers)
                print r.text
                if r.json().get('fills'):
                    for fill in list(r.json()['fills']):
                        if r.json()['direction'] == 'buy':
                            totalCash -= fill['price']*fill['qty']
                            netFilledOrders += fill['qty']
                        elif r.json()['direction'] == 'sell':
                            totalCash += fill['price']*fill['qty']
                            netFilledOrders -= fill['qty']
                orders.pop(0)
            print ('bid: %s, ask: %s, position: %s total Cash: %s Stock Value: %s Net Value: %s' % (bid, ask, pos, totalCash, netFilledOrders*bid, totalCash + netFilledOrders*bid))
    

def delete_order(order_id):
    r = requests.delete(url+'/orders/%s' % order_id, headers=headers)
    print 'canceled order %s ' % r.json()['id']

def remove_filled_orders(orders, totalCash, netFilledOrders):
    for i, order_id in enumerate(orders):
        r = requests.get(url+'/orders/%s' % order_id, headers=headers).json()
        if r['originalQty'] == r['totalFilled']:
            delete_order(order_id)
            if r.get('fills'):
                for fill in list(r['fills']):
                    if r['direction'] == 'buy':
                        totalCash -= fill['price']*fill['qty']
                        netFilledOrders += fill['qty']
                    elif r['direction'] == 'sell':
                        totalCash += fill['price']*fill['qty']
                        netFilledOrders -= fill['qty']
            del orders[i]
    return totalCash, netFilledOrders

#def listen_websocket():
#    from websocket import create_connection
#    socket_str = 'wss://api.stockfighter.io/ob/api/ws/%s/venues/%s/executions' % (account, venue)
#    ws = create_connection(socket_str)
#    while 1:
#        sleep(0.5)
#        result =  ws.recv()
#        print type(result) 

def get_position(stock=stock, venue=venue, account=account, key=key):
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

if __name__ == '__main__':
    def Gspawn():
        #G = [spawn(run_MarketMaker), spawn(listen_exec)]
        G = [spawn(run_limit)]
        [g.join() for g in G]
                
    P = [Process(target=Gspawn)]
    [p.start() for p in P]
    [p.join() for p in P]  
