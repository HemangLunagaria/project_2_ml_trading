### 
# This script is scheduled, like a Cron Job, that will run at 1st minute of every hour to get the OHLC data for that hour, generate buy/sell signals for the coins, save the signals as CSV, upload it to S3 bucket and execute the latest signal for the coins using Kraken exchange.
# Execute this script from Data_ML_models_training folder and run python CronJobs/predictions.py command. This is important because this way current working directory gets set to Data_ML_models_training directory.
# ###

import os
import sys
import asyncio
import pandas as pd
import schedule
import time
import boto3
import json
if sys.platform.startswith('darwin'): # Mac OS specific lib
    import pync #Lib to show Mac OS notification.

from botocore.exceptions import ClientError
from datetime import datetime
from sklearn.pipeline import make_pipeline, Pipeline
from joblib import load
from dotenv import load_dotenv

# Run this to for following imports to work when executing via termimal
from Exchange_Integration import kraken_integration as kr
from Utility_Functions import Functions

# Load environment variables
load_dotenv()

# Import environment variables
aws_public_key = os.getenv("AWS_TRADINATOR_KEY")
aws_secret_key = os.getenv("AWS_TRADINATOR_SECRET")

# Setting global variables
s3_bucket = 'tradinator'

currs_list = ['ETH/AUD', 'XRP/AUD' , 'LTC/AUD', 'ADA/AUD', 'XLM/AUD', 'BCH/AUD', 'BTC/AUD']     #List of supported cryptocurrencies
indicators_list = ['SMA_agg', 'RSI_ratio', 'CCI', 'MACD_ratio', 'ADX', 'ADX_dirn', 'ATR_ratio', 'BBands_high', 'BBands_low', 'SMA_vol_agg', 'Returns'] #List of indicators on which the ML models have been trained
since = 1630540800000 #EPOCH time in milliseconds for date 02/09/2021 00:00:00 GMT. This is a reference point as the ML model has been trained till 01/09/2021 data.
with open("./Resources/autotrading_config.json") as jsonFile: #Reading the config file required for autotrading
    trading_config = json.load(jsonFile)
    jsonFile.close()

# boto3 client to upload files to S3
s3_client = boto3.client(
    's3',
    aws_access_key_id = aws_public_key,
    aws_secret_access_key = aws_secret_key,
    region_name = 'us-west-2'
)

# Creates MAC OS notification when the job finishes
def createNotification():
    title = 'Tradinator Cron Job'
    if sys.platform.startswith('darwin'):
        pync.notify(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ":Predictions generated and uploaded to S3", title=title, group=os.getpid())

# Gets the joblib file uploaded to S3 and saves it to Resources folder
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

# Uploads the file to S3 at the given destination
def uploadFileToS3(file, folder):
    try:
        response = s3_client.upload_file(file, s3_bucket, folder)
        return True
    except ClientError as e:
        return False

# Calculates technical indicators for the OHLC data for each supported currency
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

# Calculates maximum volume which can be bought based on given amount (IN AUD) and latest bid price (IN AUD) of that coin.
def calculateVolumeToBuy(amount, pair):
    bid = kr.getBidPrice(pair)
    return float(amount/bid)

# Gets the volume of the selected cryptocurrency available in the user's portfolio on Kraken exchange. 
def calculateVolumeToSell(bal_id, total_balance):
    if bal_id in total_balance.keys():
        # print(float(result[coin]))
        return float(total_balance[bal_id])
    return float(0)

###
# Checks whether the buy signal for a coin is executable or not based on following conditions:
# 1. AUD balance is available and is equal or greater than the amount of AUD to invest which is provided by the config file
# 2. Volume that can be bought is more than or equal to minimum volume for that coin. Minimum volume is set up in the config file.
# 3. If the crypto's balance in Kraken is 0 or it doesn't exist at all in the balance dictionary that gets returned by the call to getMyBalance in kraken_integration.py
# ###
def isBuySignalExecutable(volume, amount, min_vol, bal_id, total_balance):
    try:
        if 'ZAUD' in total_balance.keys() and (bal_id not in total_balance.keys() or (bal_id in total_balance.keys() and float(total_balance[bal_id]) == float(0))):
            if float(total_balance['ZAUD']) >= amount and volume >= min_vol :
                return True
    except Exception as ex:
        print(ex)
        return False
    return False

### 
# Checks whether the sell signal is executable based on following conditon:
# 1. If the crypto's balance in Kraken is more than 0 in the balance dictionary that gets returned by the call to getMyBalance in kraken_integration.py
# ###
def isSellSignalExecutable(volume):
    if volume > 0:
        return True
    return False

### 
# Places market sell order for the selected crypto
# ###
def placeSellOrder(pair, volume):
    result = kr.placeOrder("market", "sell", pair, volume=volume)
    print(pair + ":" + str(result))

### 
# Places market buy order for the selected crypto
# ###
def placeBuyOrder(pair, volume):
    result = kr.placeOrder("market", "buy", pair, volume=volume)
    print(pair + ":" + str(result))

### 
# Asynchronously executes the trade for the crypto based on config value set. It does the following:
# 1. Change pair format to remove / eg. ETH/AUD -> ETHAUD for placing msrket order
# 2. To check balance for a coin, different format is required. Eg AUD -> ZAUD, BTC -> XXBT
# 3. Figure out volume to buy/sell
# 4. Check if signal is executable
# 5. Execute it if possible
# ###
async def executeTrade(curr, signal):
    try:
        volume = 0
        amount = float(trading_config[curr]['amount'])
        min_vol =  float(trading_config[curr]['min_vol'])
        bal_id = trading_config[curr]['bal_id']
        pair = trading_config[curr]['pair']
        total_balance = kr.getMyBalance()
        print(curr + " : " + str(signal))
        if signal == 1: #BUY or HOLD
            volume = calculateVolumeToBuy(amount, pair)
            print(volume, amount, min_vol, bal_id, total_balance)
            if isBuySignalExecutable(volume, amount, min_vol, bal_id, total_balance):
                placeBuyOrder(pair, volume)
            else:
                print(curr + ": BUY NOT POSSIBLE" )
        elif signal == 0: #DONT BUY or SELL
            volume = calculateVolumeToSell(bal_id, total_balance)
            if isSellSignalExecutable(volume):
                placeSellOrder(pair, volume)
            else:
                print(curr + ": SELL NOT POSSIBLE" )
    except Exception as ex:
        print(ex)

### 
# Asynchronously generates the predictions for each coin, executes the trade for the crypto based on the latest prediction. It does the following: 
# Gets OHlC data for the crypto
# Calculate technical indicators
# Generate predictions using joblib file
# Execute the trade
# Generate CSV to save the generated predictions
# Upload CSV to S3 bucket for Lex bot
# ###
async def getPredictionsPerCoin(curr, since, pipeline):
    csv_filename = curr.replace('/','-') + '_predictions.csv'
    csv_path = 'Resources/' + csv_filename
    df = kr.getOHLC_CCXT(curr, since)
    df_tech_indicators = calculateIndicators(curr, df)
    X_data = df_tech_indicators.loc[:, indicators_list].reset_index(drop=True)
    y_data = df_tech_indicators.loc[:, ['Currency']].copy()
    y_data['Predictions'] = pipeline.predict(X_data)
    await executeTrade(curr,y_data['Predictions'][-1])
    y_data.to_csv(csv_path)
    result = uploadFileToS3(csv_path, 'predictions/' + csv_filename)
    return curr + " predictons generated and uploaded." if result else curr + " predictons generated but not uploaded."

### 
# Creates task to run getPredictionsPerCoin for each crypto
# ###
async def getPredictions_async(joblib):
    tasks = []
    for curr in currs_list:
        task = asyncio.create_task(getPredictionsPerCoin(curr, since, joblib))
        tasks.append(task)
    # print(tasks)
    return await asyncio.gather(*tasks)

### 
# Calls asyncio to run the tasks and gather the final result of each task
# ###
def predictions_async(joblib):
    results = ""
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(getPredictions_async(joblib))
    return results

### 
# Sync method to get the data. Not used anywhere. Created to test how long it takes to run synchronously
# ###
def getData_sync():
    ohlc_data_dict = {}
    for curr in currs_list:
        df = kr.getOHLC_CCXT(curr, since)
        ohlc_data_dict[curr] = df
        # ohlc_data_dict[curr] = df
    return ohlc_data_dict

### 
# Main function that gets scheduled to 1st minute of every hour
# ###
def predictions(file=None):
    print("-------------Starting job:" + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '-------------')
    if file is not None:
        results = ""
        results = predictions_async(file)
        print(results)
        createNotification()
    else:
        print("Provide a joblib file to continue")
    print("-------------Ending job:" + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '-------------')
    return results
    
def printcwd():
    print(os.getcwd())

joblib_files = getJobLibFile() # Fetches the joblib from S3 bucket
joblib_file = load('Resources/' + joblib_files[0])
schedule.every().hour.at("01:00").do(predictions, file=joblib_file) # Schedules the job to run first minute of every hour
# schedule.every(2).minutes.do(predictions, file=joblib_file)

while True:
    schedule.run_pending()
    time.sleep(1)