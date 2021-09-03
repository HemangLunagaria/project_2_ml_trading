import json
import boto3
import datetime
from dateutil import tz
import csv    

def getPredictedSignals():
    bucket = 'tradinator'
    currencyList = ['ADA-AUD_predictions','BCH-AUD_predictions','ETH-AUD_predictions', 'LTC-AUD_predictions', 'XLM-AUD_predictions', 'XRP-AUD_predictions', 'BTC-AUD_predictions'] 
    # key='predictions/ADA-AUD_predictions.csv'
    # from_zone = tz.gettz('UTC')
    # to_zone = tz.gettz('Australia/Melbourne')
    
    results = ""
    	
    for curr in currencyList:
        key = 'predictions/' + curr + '.csv'
        s3_resource = boto3.resource('s3')
        s3_object = s3_resource.Object(bucket, key)
        
        data = s3_object.get()['Body'].read().decode('utf-8').splitlines()
        
        lines = csv.reader(data)
        headers = next(lines)
        rows=[]
        # print('headers: %s' %(headers))
        for line in lines:
            rows.append(line)
            
        total_rows = len(rows)
        # print(total_rows)
        # dt = datetime.datetime.strptime(rows[total_rows-1][0], '%Y-%m-%d %H:%M:%S')
        # dt = dt.replace(tzinfo=from_zone)
        # # Convert time zone
        # dt = dt.astimezone(to_zone)
        # results.append([dt, rows[total_rows-1][1], rows[total_rows-1][2]])
        if rows[total_rows-1][2] == '1':
            results = results + '\n' + rows[total_rows-1][1] + ": Buy or Hold,"
        elif rows[total_rows-1][2] == '0':
            results = results + '\n' + rows[total_rows-1][1] + ": Don't Buy or Sell,"
    # print(dt, rows[total_rows-1][1], rows[total_rows-1][2])
    return results