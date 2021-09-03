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
sys.path.append("../Exchange_Integration/")
sys.path.append("../Utility_Functions/")
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
since = 1629936000000 #EPOCH time in milliseconds for date 26/08/2020 00:00:00 GMT. This is a reference point.
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

async def getPredictionsPerCoin(curr, since, pipeline):
    csv_filename = curr.replace('/','-') + '_predictions.csv'
    csv_path = 'Resources/' + csv_filename
    df = kr.getOHLC_CCXT(curr, since)
    df_tech_indicators = calculateIndicators(curr, df)
    X_data = df_tech_indicators.loc[:, indicators_list].reset_index(drop=True)
    y_data = df_tech_indicators.loc[:, ['Currency']].copy()
    y_data['Predictions'] = pipeline.predict(X_data)
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