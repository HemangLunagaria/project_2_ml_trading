# This is a cron job that will run every 60th minute to get the OHLC data for that hour and generate buy/sell signals for the coins, save the signals as CSV and upload it to S3 bucket.

import os
import sys
import asyncio
import pandas as pd
import schedule
import time
import boto3
if sys.platform.startswith('darwin'):
    import pync

from botocore.exceptions import ClientError
from datetime import datetime
from sklearn.pipeline import make_pipeline, Pipeline
from joblib import load
from dotenv import load_dotenv

# Run this to for following imports to work when executing via termimal
# export PYTHONPATH="${PYTHONPATH}:/Users/hemanglunagaria/Documents/Monash_FinTech_repos/project_2_ml_trading/"
from Exchange_Integration import kraken_integration as kr
from Utility_Functions import Functions

# Load environment variables
load_dotenv()

# Import environment variables
aws_public_key = os.getenv("AWS_TRADINATOR_KEY")
aws_secret_key = os.getenv("AWS_TRADINATOR_SECRET")

s3_bucket = 'tradinator'

currs_list = ['ETH/AUD', 'XRP/AUD' , 'LTC/AUD', 'ADA/AUD', 'XLM/AUD', 'BCH/AUD', 'BTC/AUD']     #
indicators_list = ['SMA_agg', 'RSI_ratio', 'CCI', 'MACD_ratio', 'ADX', 'ADX_dirn', 'ATR_ratio', 'BBands_high', 'BBands_low', 'SMA_vol_agg', 'Returns']
since = 1630540800000 #EPOCH time in milliseconds for date 02/09/2021 00:00:00 GMT. This is a reference point.
tasks = []

s3_client = boto3.client(
    's3',
    aws_access_key_id = aws_public_key,
    aws_secret_access_key = aws_secret_key,
    region_name = 'us-west-2'
)

def createNotification():
    title = 'Tradinator Cron Job'
    if sys.platform.startswith('darwin'):
        pync.notify(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ":Predictions generated and uploaded to S3", title=title, group=os.getpid())

def getJobLibFile():
    s3_folder = 'joblib' 
    os.chdir('Resources')

    response = s3_client.list_objects(Bucket=s3_bucket)
    joblib_files = []
    for obj in response['Contents']:
        foldername = obj['Key'].split('/')[0]
        filename = obj['Key'].split('/')[1]
       
        if foldername == s3_folder and len(filename) > 0:
            s3_client.download_file(s3_bucket, obj['Key'], filename)
            joblib_files.append(filename)
    os.chdir("..")
    return joblib_files

def uploadFileToS3(file, folder):
    try:
        response = s3_client.upload_file(file, s3_bucket, folder)
        return True
    except ClientError as e:
        return False

def calculateIndicators(curr, data):
    fast_window = 5
    slow_window = 15

    df_data = pd.DataFrame() 
    # for curr, data in ohlcv_dict.items():

    df = Functions.add_tech_indicators(data, fast_window, slow_window)
    
    df['Currency'] = curr 
    df['Returns'] = df['Close'].pct_change()

    df.dropna(inplace=True)    
    df_data = df_data.append(df)

    return df_data

def get_coin_codes(coin):

    # TODO: This is required because the balance api in kraken returns the balances in a different code format 
    if coin == 'BTC': code = 'XXBT'
    elif coin == 'ETH': code = 'ETH'
    elif coin == 'XLM': code = 'XXLM'
    elif coin == 'XRP': code = 'XRP'
    elif coin == 'ADA': code = 'ADA'
    elif coin == 'BCH': code = 'BCH'
    elif coin == 'LTC': code = 'LTC'

    return code 

def get_amount_per_position():

    amount = 50
    # TODO: Read the parameter set in csv / JSON
    return amount 

def getBalance(coin):
    result = kr.getMyBalance()
    balance = ""
    for key, data in result.items():
        balance = balance + "[" + key + ":" + data + "], "
    return balance

def placeSellOrder(pair, volume):
    kr.placeOrder("market", "sell", pair, volume=volume)

def placeBuyOrder(pair, volume):
    kr.placeOrder("market", "buy", pair, volume=volume)

def executeTrade(pair, signal):
    # TODO : Change pair format to remove / eg. ETH/AUD -> ETHAUD
    # TODO : To check balance for a coin, different format is required. Eg AUD -> ZAUD, BTC -> XXBT
    # TODO : Figure out volume to buy/sell
    # TODO : Check if enough cash balance available to buy the given volume of the coin

    # Sid - We can get the whole account balance here. the Endpoint can be called once and the relevant balance can be passed further 
    balance = kr.getMyBalance()

    # Read the balances fetched earlier in this function  
    coin, aud = pair.split('/')

    coin_vol = aud_bal = 0

    if get_coin_codes(coin) in balance.keys(): coin_vol = float(balance[coin])
    if 'ZAUD' in balance.keys(): aud_bal = float(balance['ZAUD'])
        
    volume = 0
    if signal == 1 and coin_vol == 0: #If we havent bought the coin yet and signal is 1, then BUY

        # further check before buying - if the current balance is greater than or equal to the amount configured by the user 
        amt_per_trade = get_amount_per_position()
        if amt_per_trade <= aud_bal:
            price = kr.getBidPrice(pair)
            volume = amt_per_trade / price
            pair = pair.replace('/', '')

            placeBuyOrder(pair, volume)

    elif signal == 0 and coin_vol > 1: #If we have the coin and the signal = 0, then SELL

        volume = coin_vol
        placeSellOrder(pair, volume)

async def getPredictionsPerCoin(curr, since, pipeline):
    csv_filename = curr.replace('/','-') + '_predictions.csv'
    csv_path = 'Resources/' + csv_filename
    df = kr.getOHLC_CCXT(curr, since)
    df_tech_indicators = calculateIndicators(curr, df)
    X_data = df_tech_indicators.loc[:, indicators_list].reset_index(drop=True)
    y_data = df_tech_indicators.loc[:, ['Currency']].copy()
    y_data['Predictions'] = pipeline.predict(X_data)

    # Sid: y_data['Predictions'][-1] can be used as the Buy/Hold/Dont buy/Sell
    signal = y_data['Predictions'][-1]
    executeTrade(curr, signal )

    y_data.to_csv(csv_path)
    result = uploadFileToS3(csv_path, 'predictions/' + csv_filename)
    return curr + " predictons generated and uploaded." if result else curr + " predictons generated but not uploaded."

async def getPredictions_async(joblib):

    for curr in currs_list:

        task = asyncio.create_task(getPredictionsPerCoin(curr, since, joblib))
        tasks.append(task)
    # print(tasks)
    return await asyncio.gather(*tasks)

def predictions_async(joblib):
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(getPredictions_async(joblib))
    return results

def getData_sync():
    
    ohlc_data_dict = {}
    for curr in currs_list:
        df = kr.getOHLC_CCXT(curr, since)
        ohlc_data_dict[curr] = df
        # ohlc_data_dict[curr] = df
    return ohlc_data_dict

def predictions(file=None):
    print("-------------Starting job:" + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '-------------')
    results = ""
    if file is not None:
        results = predictions_async(file)
        print(results)
        createNotification()
    else:
        print("Provide a joblib file to continue")
    print("-------------Ending job:" + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '-------------')
    return results
    
def printcwd():
    print(os.getcwd())

joblib_files = getJobLibFile()
joblib_file = load('Resources/' + joblib_files[0])
schedule.every().hour.at("01:00").do(predictions, file=joblib_file)
# schedule.every(2).minutes.do(predictions, file=joblib_file)

while True:
    schedule.run_pending()
    time.sleep(1)