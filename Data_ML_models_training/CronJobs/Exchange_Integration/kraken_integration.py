### 
# Integration with Kraken exchange using their REST API. 
# Refer : https://docs.kraken.com/rest/
# ###

import os
import urllib.parse
import hashlib
import hmac
import base64
import requests
import ccxt
import pandas as pd

from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Import environment variables
kraken_public_key = os.getenv("KRAKEN_PUBLIC_KEY")
kraken_secret_key = os.getenv("KRAKEN_SECRET_KEY")

endpoint = "https://api.kraken.com"

# Function to generate signature as per Kraken's requirements
# https://docs.kraken.com/rest/#section/Authentication/Headers-and-Signature
def getSignature(urlpath, data):

    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(kraken_secret_key), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

# Function to get the auth headers
def getHeaders(urlpath, params) :
    headers = {}
    headers['API-Key'] = kraken_public_key
    headers['API-Sign'] = getSignature(urlpath, params)

    return headers

# Function to execute POST request
def executePostRequest(url, headers, params, key):
    try:
        response = requests.post(url, headers=headers, data=params)
        result = response.json() #json.loads(response.text)
        if len(result['error']) == 0:
            return result[key]
        else :#result['status'].lower() == 'error':
            raise requests.RequestException(result["error"])
    except requests.RequestException as ex:
        return "error:" + str(ex)
    except Exception as ex:
        return "error:" + str(ex)

# Function to execute GET request
def executeGetRequest(url, key, headers=None, params=None):
    try:
        response = ""
        if headers == None and params == None:
            response = requests.get(url)
        else:
            response = requests.get(url, headers=headers, params=params)
        
        result = response.json()
        if len(result['error']) == 0:
            return result[key]
        else :#result['status'].lower() == 'error':
            raise requests.RequestException(result["error"])
    except requests.RequestException as ex:
        return "error:" + str(ex)
    except Exception as ex:
        return "error:" + str(ex)

# Function to fetch OHLC data from Kraken API
# pair : Pair to get OHLC data for eg: ADAAUD
# since : EPOCH value
def getOHLC(pair, since):
    url = endpoint + '/0/public/OHLC'
    postdata = {}
    postdata['pair'] = pair.upper()
    postdata['interval'] = 60
    postdata['since'] = str(since)
    result = executeGetRequest(url,'result', {}, postdata)
    return result

# Sample resposne: {'ADAAUD': {'a': ['3.840700', '2916', '2916.000'], 'b': ['3.801550', '2942', '2942.000'], 'c': ['3.841090', '8.29470281'], 'v': ['6392.70596342', '23560.39983444'], 'p': ['3.819036', '3.824366'], 't': [44, 116], 'l': ['3.743660', '3.743660'], 'h': ['3.871730', '3.929740'], 'o': '3.770460'}}
# 'a'  stands for ask and 'b' stands for bid
# Reference : https://docs.kraken.com/rest/#operation/getTickerInformation
def getTickerInformation(pair):
    url = endpoint + '/0/public/Ticker'
    postdata = {}
    postdata['pair'] = pair.upper()
    result = executeGetRequest(url,'result', {}, postdata)
    return result

# Get ask price == sell
def getAskPrice(pair):
    data = getTickerInformation(pair)
    price_data = data[pair]
    ask_price = price_data['a'][0]
    return float(ask_price)

# Get bid price == buy
def getBidPrice(pair):
    data = getTickerInformation(pair)
    price_data = data[pair]
    bid_price = price_data['b'][0]
    return float(bid_price)

# Using ccxt library to get OHLC candles
def getOHLC_CCXT(pair, since):
    exchange = ccxt.kraken({
        'apiKey': kraken_public_key,
        'secret': kraken_secret_key,
    })

     # Call data fetch
    ohlcv = exchange.fetchOHLCV(pair.upper(), '1h', since=since)

    # Store the values in a dataframe
    df_ohlcv = pd.DataFrame(ohlcv, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume']).set_index('Date')
    df_ohlcv.index = pd.to_datetime(df_ohlcv.index, unit='ms')

    df_ohlcv.dropna(inplace=True)
    return df_ohlcv

# Function to fetch the user balance from Kraken
def getMyBalance():
    nonce = int(1000*time.time())
    postdata = {}
    postdata['nonce'] = str(nonce)
    urlpath = '/0/private/Balance'
    headers = getHeaders(urlpath, postdata)
    url = endpoint + urlpath
    result = executePostRequest(url, headers, postdata, 'result')
    return result

def getCashBalance():
    result = getMyBalance()
    if 'ZAUD' in result.keys():
        return float(result['ZAUD'])
    return float(0)


# Function to place order on Kraken
# ordertype: Values can be one of the following("market" "limit" "stop-loss" "take-profit" "stop-loss-limit" "take-profit-limit" "settle-position")
# type : Values can be one of the following("buy" "sell")
# pair : Coin to buy eg ADAAUD
# price: Limit price for limit orders or Trigger price for stop-loss, stop-loss-limit, take-profit and take-profit-limit orders
# volume : Order quantity
def placeOrder(ordertype, type, pair, price=0, volume=0):
    nonce = int(1000*time.time())
    postdata = {}
    postdata['nonce'] = str(nonce)
    postdata['ordertype'] = ordertype.lower()
    postdata['type'] = type.lower()
    postdata['volume'] = volume
    postdata['pair'] = pair.upper()
    postdata['price'] = price
    urlpath = '/0/private/AddOrder'
    headers = getHeaders(urlpath, postdata)
    url = endpoint + urlpath
    result = executePostRequest(url, headers, postdata, 'result')
    return result
    