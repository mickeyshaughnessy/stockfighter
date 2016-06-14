import requests
from json import dumps
from config import *

headers = {"X-Starfighter-Authorization": key}

soln = {}
soln['account'] = 'FFB93850575'
soln['explanation_link'] = ''
soln['executive_summary'] = ''

url = 'https://www.stockfighter.io/gm/instances/30717'
url = url + '/judge'

resp = requests.post(url, data=dumps(soln), headers=headers)
print resp.json()
