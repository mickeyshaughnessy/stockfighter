# this script deploys a market maker 
"""
curl https://api.stockfighter.io/ob/api/venues/AIOPEX/stocks/MEIA/quote --header "X-Starfighter-Authorization:d4f6f80befe9cd49a65f470a1acea0bb227a104b"
curl -X POST -d '{"orderType":"market","qty":1,"direction":"buy","account":"WLS28175343"}' https://api.stockfighter.io/ob/api/venues/MRBTEX/stocks/OGV/orders --header "X-Starfighter-Authorization:d4f6f80befe9cd49a65f470a1acea0bb227a104b"
"""

import requests
import json
from gevent import spawn, sleep
from multiprocessing import Process

account = "SAH91522616"
key = "d4f6f80befe9cd49a65f470a1acea0bb227a104b"
stock = "TMHM"
venue = "UQSPEX"
url = 'https://api.stockfighter.io/ob/api/venues/%s/stocks/%s' % (venue, stock)
headers = {"X-Starfighter-Authorization": "d4f6f80befe9cd49a65f470a1acea0bb227a104b"}
payload_buymarket = json.dumps({"orderType":"market","qty":1,"direction":"buy","account":account})


last_buy, last_sell, pos = 50, 50, 0

def quote():
    r = requests.get(url+'/quote', headers=headers)
    try:
        bid, ask = r.json().get('ask'), r.json().get('bid')
    except:
        print r.text
    return bid, ask
 
def run_MarketMaker():
    bid, ask = quote()
    last_buy, last_sell, pos = 50, 50, 0
    while 1:
        sleep(1)
        bid, ask = quote()
        print bid, ask
        if bid and ask and pos < 400 and pos > -400:
            if (bid > last_buy):
                cost = max(last_sell, bid)
                payload_selllimit = json.dumps({"orderType":"limit", "price":int(cost),"qty":10,"direction":"sell","account":account})
                r1 = requests.post(url+'/orders', data=payload_selllimit, headers=headers)
                pos -= int(r1.json()['qty'])
                last_sell = int(r1.json()['price'])
            
            if (ask < last_sell):
                cost = min(last_buy, ask)
                payload_buylimit = json.dumps({"orderType":"limit","price":int(cost),"qty":10,"direction":"buy","account":account})
                r2 = requests.post(url+'/orders', data=payload_buylimit, headers=headers)
                pos += int(r2.json()['qty'])
                last_buy = int(r2.json()['price'])
        else:
            print bid, ask

def listen_exec():
    from websocket import create_connection
    socket_str = 'wss://api.stockfighter.io/ob/api/ws/%s/venues/%s/executions' % (account, venue)
    ws = create_connection(socket_str)
    while 1:
        sleep(0.5)
        result =  ws.recv()
        print type(result) 

if __name__ == '__main__':
    def Gspawn():
        G = [spawn(run_MarketMaker), spawn(listen_exec)]
        [g.join() for g in G]
                
    P = [Process(target=Gspawn)]
    [p.start() for p in P]
    [p.join() for p in P]  
