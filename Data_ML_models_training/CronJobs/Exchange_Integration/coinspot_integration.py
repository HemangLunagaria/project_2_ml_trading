### Integration with CoinSpot exchanges using their REST API. 
# Refer https://www.coinspot.com.au/api for more information
# ###

import os
import hmac
import hashlib
import requests
import json

from dotenv import load_dotenv
from time import time

# Load environment variables
load_dotenv()

# Import environment variables
coinspot_public_key = os.getenv("COINSPOT_PUBLIC_KEY")
coinspot_secret_key = os.getenv("COINSPOT_SECRET_KEY")

private_endpoint = "https://www.coinspot.com.au/api"
public_endpoint = "https://www.coinspot.com.au/pubapi"

### 
# Generates signature as per CoinSpot's requirements
# Refer : https://www.coinspot.com.au/api#security
# ###
def getSignature(params):
    return hmac.new(bytes(coinspot_secret_key, 'utf-8'), bytes(params, 'utf-8'), hashlib.sha512).hexdigest()

### 
# Generates headers required for each API call based on parameters for that API call
# ###
def getHeaders(params) :
    headers = {}
    headers['Content-type'] = 'application/json'
    headers['Accept'] = 'text/plain'
    headers['key'] = coinspot_public_key
    headers['sign'] = getSignature(params)

    return headers

### 
# POST method execution using requests lib
# Each response JSON message has a status attribute to it.
# ###
def executePostRequest(url, headers, params, key):
    try:
        response = requests.post(url, headers=headers, data=params)
        result = json.loads(response.text)
        if result['status'].lower() == 'ok':
            return result[key]
        elif result['status'].lower() == 'error':
            raise requests.RequestException(result["message"])
    except requests.RequestException as ex:
        return "error:" + str(ex)
    except Exception as ex:
        return "error:" + str(ex)

### 
# GET method execution using requests lib
# ###
def executeGetRequest(url, key, headers=None, params=None):
    try:
        response = ""
        if headers == None and params == None:
            response = requests.get(url)
        else:
            response = requests.get(url, headers=headers, params=params)
        
        result = json.loads(response.text)
        if result['status'].lower() == 'ok':
            return result[key]
        elif result['status'].lower() == 'error':
            raise requests.RequestException(result["message"])
    except requests.RequestException as ex:
        return "error:" + str(ex)
    except Exception as ex:
        return "error:" + str(ex)

### 
# Gets the latest price for a crypto
# Refer : https://www.coinspot.com.au/api#latestprices
# ###
def getLatestPrice(coin):
    url = public_endpoint + "/latest"
    result = executeGetRequest(url, "prices")
    return result[coin]

### 
# Gets the balance available in user's CoinSpot account
# Refer : https://www.coinspot.com.au/api#listmybalance
# ###
def getMyBalance():
    nonce = int(time()*1000000)
    postdata = {}
    postdata['nonce'] = nonce
    params = json.dumps(postdata, separators=(',', ':'))
    headers = getHeaders(params)
    url = private_endpoint + "/my/balances"
    result = executePostRequest(url, headers, params, 'balance')
    return result
    
### 
# Function to place buy order. CoinSpot API do not support market order so for each buy order, price needs to be quoted. In order to simplify the execution and simulate market order, latest bid price is fetched for that coin and is used to prvide it as the rate at which to buy the coin.
# Refer : https://www.coinspot.com.au/api#placebuyorder
# ###
def placeBuyOrder(coin, amount):
    rate = getLatestPrice(coin.lower())['bid']
    nonce = int(time()*1000000)
    postdata = {}
    postdata['cointype'] = coin.upper()
    postdata['amount'] = amount
    postdata['rate'] = rate
    postdata['nonce'] = nonce
    params = json.dumps(postdata, separators=(',', ':'))
    headers = getHeaders(params)
    url = private_endpoint + "/my/buy"
    result = executePostRequest(url, headers, params, 'status')
    return result

### 
# Function to place sell order. CoinSpot API do not support market order so for each sell order, price needs to be quoted. In order to simplify the execution and simulate market order, latest ask price is fetched for that coin and is used to prvide it as the rate at which to buy the coin.
# Refer : https://www.coinspot.com.au/api#placesellorder
# ###
def placeSellOrder(coin, amount):
    rate = getLatestPrice(coin.lower())['ask']
    nonce = int(time()*1000000)
    postdata = {}
    postdata['cointype'] = coin.upper()
    postdata['amount'] = amount
    postdata['rate'] = rate
    postdata['nonce'] = nonce
    params = json.dumps(postdata, separators=(',', ':'))
    headers = getHeaders(params)
    url = private_endpoint + "/my/sell"
    result = executePostRequest(url, headers, params, 'status')
    return result