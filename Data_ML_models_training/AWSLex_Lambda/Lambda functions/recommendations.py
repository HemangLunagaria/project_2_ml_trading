import json
import boto3
import datetime
from dateutil import tz
import csv    

# Function to fetch predictions of each coin from respective CSV uploaded to S3 bucket and return the latest prediction as recommendations to pass onto Lex bot.
def getPredictedSignals():
    bucket = 'tradinator'
    currencyList = ['ADA-AUD_predictions','BCH-AUD_predictions','ETH-AUD_predictions', 'LTC-AUD_predictions', 'XLM-AUD_predictions', 'XRP-AUD_predictions', 'BTC-AUD_predictions'] #List of name of files that are uploaded to S3 without extension
    
    results = ""
    	
    # For loop to traverse through the list for get latest predictions ans return a concatenated message back to the bot
    for curr in currencyList:
        key = 'predictions/' + curr + '.csv'
        s3_resource = boto3.resource('s3')
        s3_object = s3_resource.Object(bucket, key) # Create S3 objecct
        
        data = s3_object.get()['Body'].read().decode('utf-8').splitlines() #Fetch the data
        
        lines = csv.reader(data)
        headers = next(lines)
        rows=[]
        for line in lines:
            rows.append(line)
            
        total_rows = len(rows)

        # Getting the last row which will be latest prediction. Predictions are updated every hour so the latest predictions will be the current hour.
        if rows[total_rows-1][2] == '1':
            results = results + '\n' + rows[total_rows-1][1] + ": Buy or Hold,"
        elif rows[total_rows-1][2] == '0':
            results = results + '\n' + rows[total_rows-1][1] + ": Don't Buy or Sell,"
    return results